#include <cstdarg>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <utility>
#include <vector>

//#define Py_LIMITED_API 0x03060000
#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "scssdk_telemetry.h"
#include "eurotrucks2/scssdk_eut2.h"
#include "eurotrucks2/scssdk_telemetry_eut2.h"
#include "amtrucks/scssdk_ats.h"
#include "amtrucks/scssdk_telemetry_ats.h"

// Handles reference counting of PyObject*
// TODO: Own file. pyhelp namespace.
class PyObjRef {
public:
    PyObjRef() : py_obj_(nullptr) {
    }
    
    explicit PyObjRef(PyObject *py_obj) : py_obj_(py_obj) {
        inc_ref();
    }

    explicit PyObjRef(const PyObjRef &other) : py_obj_(other.py_obj_) {
        inc_ref();
    }

    explicit PyObjRef(PyObjRef &&other) : py_obj_(other.py_obj_) {
        other.py_obj_ = nullptr;
    }

    PyObjRef &operator=(const PyObjRef &other) {
        if (&other != this) {
            py_obj_ = other.py_obj_;
            inc_ref();
        }
        return *this;
    }

    ~PyObjRef() {
        dec_ref();
    }

    PyObject *get() {
        return py_obj_;
    }

    void set(PyObject *py_obj) {
        if (py_obj != py_obj_) {
            dec_ref();
            py_obj_ = py_obj;
            inc_ref();
        }
    }

    void reset() {
        set(nullptr);
    }

    /*// Force increment. Use after "loading" the pointer using ref()
    void inc() {
        inc_ref();
    }

    PyObject *&ref() {
        return py_obj_;
    }*/
private:
    void inc_ref() {
        if (py_obj_ != nullptr) {
            Py_INCREF(py_obj_);
        }
    }

    void dec_ref() {
        if (py_obj_ != nullptr) {
            Py_DECREF(py_obj_);
        }
    }
    
    PyObject *py_obj_;
};


static scs_log_t scs_log_ = nullptr;
static scs_telemetry_register_for_channel_t scs_register_for_channel_ = nullptr;
static PyObjRef py_module_;
static PyThreadState *py_thread_state_ = nullptr;

struct cb_context {
    PyObjRef py_callback;
    PyObjRef py_context;
};
static std::vector<cb_context> registered_callbacks_;

static void log(const std::string &prefix, const char *format, va_list ap) {
    std::string buf(prefix);
    buf.resize(128);
    vsnprintf(buf.data() + prefix.size(), buf.size() - prefix.size(), format, ap);
    scs_log_(SCS_LOG_TYPE_message, buf.c_str());
}

static void log(const std::string &prefix, const char *format, ...)
    __attribute__ ((format (printf, 2, 3)));
static void log(const std::string &prefix, const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    log(prefix, format, ap);
    va_end(ap);
}

static void log_loader(const char *format, ...)
    __attribute__ ((format (printf, 1, 2)));
static void log_loader(const char *format, ...) {
    static const std::string prefix = "PyETS2 Telemetry Loader: ";
    va_list ap;
    va_start(ap, format);
    log(prefix, format, ap);
    va_end(ap);
}

static void log_py(const char *message) {
    static const std::string prefix = "PyETS2 Telemetry: ";
    log(prefix, "%s", message);
}


// Python call helpers
namespace pyhelp {

// Equivalent to PyErr_Print()
void log_and_clear_py_err() {
    PyObject *py_err_type, *py_err_value, *py_err_traceback;
    PyErr_Fetch(&py_err_type, &py_err_value, &py_err_traceback);
    PyErr_NormalizeException(&py_err_type, &py_err_value, &py_err_traceback);
    PyObjRef py_err_string(PyObject_Str(py_err_value));
    const char *err_value = PyUnicode_AsUTF8AndSize(py_err_string.get(), nullptr);
    // TODO: Handle stack trace
    log_loader("%s: %s", reinterpret_cast<PyTypeObject*>(py_err_type)->tp_name, err_value);
    Py_XDECREF(py_err_type);
    Py_XDECREF(py_err_value);
    Py_XDECREF(py_err_traceback);
    PyErr_Clear();
}

template <class ... Args>
bool try_call_function(PyObject *py_func, const char *arg_format, Args... args) {
    if (py_func == nullptr || !PyCallable_Check(py_func)) {
        log_loader("Not a function");
        return false;
    }
    PyObjRef py_args(Py_BuildValue(arg_format, args...));
    PyObjRef ret(PyObject_CallObject(py_func, py_args.get()));
    if (ret.get() == nullptr) {
        log_and_clear_py_err();
        return false;
    }
    return true;
}

template <class ... Args>
bool try_call_function(const char *name, const char *arg_format, Args... args) {
    PyObjRef py_func(PyObject_GetAttrString(py_module_.get(), name));
    bool ok = try_call_function(py_func.get(), arg_format, args...);
    if (!ok) {
        log_loader("Calling function %s failed", name);
    }
    return ok;
}

bool try_call_function(const char *name) {
    return try_call_function(name, "()");
}

}


// telemetry Python module

SCSAPI_VOID telemetry_channel_cb(const scs_string_t name, const scs_u32_t index, const scs_value_t *const value, const scs_context_t context) {
    int context_index = reinterpret_cast<intptr_t>(context);
    if (context_index >= static_cast<ssize_t>(registered_callbacks_.size())) {
        log_loader("ERROR! context_index=%d > size()=%zu. Ignoring callback.",
                   context_index, registered_callbacks_.size());
        return;
    }
    cb_context &context_val = registered_callbacks_[context_index];
    
    PyEval_RestoreThread(py_thread_state_);

    { // Make sure no PyObjRef ref counting happens after PyEval_SaveThread()
        PyObjRef py_value(Py_None);
        // value might be NULL if user has set SCS_TELEMETRY_CHANNEL_FLAG_no_value
        if (value != nullptr) {
            switch (value->type) {
                case SCS_VALUE_TYPE_bool:
                    py_value.set(PyBool_FromLong(value->value_bool.value));
                    break;
                case SCS_VALUE_TYPE_s32:
                    py_value.set(PyLong_FromLong(value->value_s32.value));
                    break;
                case SCS_VALUE_TYPE_u32:
                    py_value.set(PyLong_FromUnsignedLong(value->value_u32.value));
                    break;
                case SCS_VALUE_TYPE_s64:
                    py_value.set(PyLong_FromLong(value->value_s64.value));
                    break;
                case SCS_VALUE_TYPE_u64:
                    py_value.set(PyLong_FromUnsignedLong(value->value_u64.value));
                    break;
                case SCS_VALUE_TYPE_float:
                    py_value.set(PyFloat_FromDouble(value->value_float.value));
                    break;
                case SCS_VALUE_TYPE_double:
                    py_value.set(PyFloat_FromDouble(value->value_double.value));
                    break;
                case SCS_VALUE_TYPE_string:
                    py_value.set(PyUnicode_FromString(value->value_string.value));
                    break;
                    // TODO: More types
                    //default:
                    // Keep None-value
                    // TODO: Exception?
            }
        }
        pyhelp::try_call_function(context_val.py_callback.get(), "sIOO", name, index, py_value.get(), context_val.py_context.get());
    }
    py_thread_state_ = PyEval_SaveThread();
}

namespace pymod {

static PyObject *log(PyObject *self, PyObject *arg) {
    char *message = PyUnicode_AsUTF8AndSize(arg, nullptr);
    if (message == nullptr) {
        PyErr_SetString(PyExc_TypeError, "Log message must be string");
        return nullptr;
    }
    log_py(message);
    Py_RETURN_NONE;
}

static PyObject *register_for_channel(PyObject *self, PyObject *args) {
    const char* name;
    scs_u32_t index;
    scs_value_type_t type;
    scs_u32_t flags;
    PyObject *py_callback;
    PyObject *py_context;
    if (!PyArg_ParseTuple(args, "sIIIOO", &name, &index, &type,
                          &flags, &py_callback,
                          &py_context)) {
        return nullptr;
    }
    cb_context context;
    context.py_callback.set(py_callback);
    context.py_context.set(py_context);
    auto context_it = registered_callbacks_.emplace(registered_callbacks_.end(),
                                                std::move(context));
    // Cannot store pointer to element in the vector, as the vector
    // reallocates when it grows. Using index instead.
    intptr_t context_index = context_it - registered_callbacks_.begin();
    SCSAPI_RESULT register_ret =
        scs_register_for_channel_(name, index, type, flags,
                                  telemetry_channel_cb,
                                  reinterpret_cast<void*>(context_index));
    if (register_ret != SCS_RESULT_ok) {
        registered_callbacks_.pop_back(); 
    }
    return PyLong_FromLong(register_ret);
}

static PyMethodDef methods[] = {
    {"log", log, METH_O,
     "Log a message to ETS2 developer console."},
    {"register_for_channel", register_for_channel, METH_VARARGS,
     "Registers callback to be called with value of specified telemetry channel."},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "telemetry", NULL, -1, methods,
    NULL, NULL, NULL, NULL
};

static PyObject *create() {
    return PyModule_Create(&module);
}

}


// SCS API

SCSAPI_RESULT scs_telemetry_init(const scs_u32_t version, const scs_telemetry_init_params_t *const params) {
    if (version != SCS_TELEMETRY_VERSION_1_01) {
        return SCS_RESULT_unsupported;
    }
    const scs_telemetry_init_params_v101_t * version_params = static_cast<const scs_telemetry_init_params_v101_t *>(params);
    scs_log_ = version_params->common.log;
    scs_register_for_channel_ = version_params->register_for_channel;
    log_loader("Initializing");

    // Set up path so the py file can be found
    std::string pwd = getenv("PWD");
    std::string plugin_dir = pwd + "/plugins";
    setenv("PYTHONPATH", plugin_dir.c_str(), 1);
    
    PyImport_AppendInittab("telemetry", &pymod::create);
    
    Py_Initialize();
    PyEval_InitThreads();

    { // Make sure no PyObjRef ref counting happens after PyEval_SaveThread()
        std::string python_module_name = "pyets2_telemetry";
        PyObjRef py_module_name(PyUnicode_DecodeFSDefaultAndSize(
                                    python_module_name.c_str(),
                                    python_module_name.size()));
        if (py_module_name.get() == nullptr) {
            log_loader("Could not create python filename string");
            Py_Finalize();
            return SCS_RESULT_generic_error;
        }
    
        log_loader("Importing python module \"%s\"", python_module_name.c_str());
        // TODO: relative import. Use "level"
        py_module_.set(PyImport_Import(py_module_name.get()));
        if (py_module_.get() == nullptr) {
            log_loader("Could not import python module");
            pyhelp::log_and_clear_py_err();
            Py_Finalize();
            return SCS_RESULT_generic_error;
        }
        log_loader("Python module imported");
        log_loader("Initialized");

        pyhelp::try_call_function("telemetry_init", "IssI",
                                  version,
                                  version_params->common.game_name,
                                  version_params->common.game_id,
                                  version_params->common.game_version);
    }

    py_thread_state_ = PyEval_SaveThread();

    return SCS_RESULT_ok;
}

SCSAPI_VOID scs_telemetry_shutdown() {
    PyEval_RestoreThread(py_thread_state_);

    log_loader("Call telemetry_shutdown");
    pyhelp::try_call_function("telemetry_shutdown");

    log_loader("Unloading");

    registered_callbacks_.clear();
    py_module_.reset();

    // All PyObjRef must be destroyed/reset before this point!
    // TODO: Class?
    Py_Finalize();

    py_thread_state_ = nullptr;

    log_loader("Unloaded");

    scs_log_ = nullptr;
    scs_register_for_channel_ = nullptr;
}
