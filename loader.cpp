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

static scs_log_t scs_log = nullptr;
static scs_telemetry_register_for_channel_t scs_register_for_channel = nullptr;
static PyObject *py_module = nullptr;
static PyThreadState *py_thread_state_ = nullptr;

struct cb_context {
    PyObject *py_callback;
    PyObject *py_context;
};
static std::vector<std::shared_ptr<cb_context>> registered_callbacks_;

static void log(const std::string &prefix, const char *format, va_list ap) {
    std::string buf(prefix);
    buf.resize(128);
    vsnprintf(buf.data() + prefix.size(), buf.size() - prefix.size(), format, ap);
    scs_log(SCS_LOG_TYPE_message, buf.c_str());
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
    PyObject *py_err_string = PyObject_Str(py_err_value);
    const char *err_value = PyUnicode_AsUTF8AndSize(py_err_string, nullptr);
    // TODO: Handle stack trace
    log_loader("%s: %s", reinterpret_cast<PyTypeObject*>(py_err_type)->tp_name, err_value);
    Py_XDECREF(py_err_string);
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
    PyObject *py_args = Py_BuildValue(arg_format, args...);
    PyObject *ret = PyObject_CallObject(py_func, py_args);
    Py_XDECREF(py_args);
    if (ret == nullptr) {
        log_and_clear_py_err();
        return false;
    }
    return true;
}

template <class ... Args>
bool try_call_function(const char *name, const char *arg_format, Args... args) {
    PyObject *py_func = PyObject_GetAttrString(py_module, name);
    bool ok = try_call_function(py_func, arg_format, args...);
    Py_XDECREF(py_func);
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
    PyEval_RestoreThread(py_thread_state_);
    cb_context *context_val = static_cast<cb_context*>(context);
    PyObject *py_value = Py_None;
    // value will be NULL if user has set SCS_TELEMETRY_CHANNEL_FLAG_no_value
    if (value != nullptr) {
        switch (value->type) {
            case SCS_VALUE_TYPE_bool:
                py_value = PyBool_FromLong(value->value_bool.value);
                break;
            case SCS_VALUE_TYPE_s32:
                py_value = PyLong_FromLong(value->value_s32.value);
                break;
            case SCS_VALUE_TYPE_u32:
                py_value = PyLong_FromUnsignedLong(value->value_u32.value);
                break;
            case SCS_VALUE_TYPE_s64:
                py_value = PyLong_FromLong(value->value_s64.value);
                break;
            case SCS_VALUE_TYPE_u64:
                py_value = PyLong_FromUnsignedLong(value->value_u64.value);
                break;
            case SCS_VALUE_TYPE_float:
                py_value = PyFloat_FromDouble(value->value_float.value);
                break;
            case SCS_VALUE_TYPE_double:
                py_value = PyFloat_FromDouble(value->value_double.value);
                break;
            case SCS_VALUE_TYPE_string:
                py_value = PyUnicode_FromString(value->value_string.value);
                break;
                // TODO: More types
                //default:
                // Keep None-value
                // TODO: Exception?
        }
    }
    pyhelp::try_call_function(context_val->py_callback, "sIOO", name, index, py_value, context_val->py_context);
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
    // TODO: Store this somewhere, for clean-up!!!
    auto context = std::make_shared<cb_context>();
    if (!PyArg_ParseTuple(args, "sIIIOO", &name, &index, &type,
                          &flags, &context->py_callback,
                          &context->py_context)) {
        return nullptr;
    }
    SCSAPI_RESULT register_ret = scs_register_for_channel(name, index, type, flags,
                                                          telemetry_channel_cb, context.get());
    if (register_ret == SCS_RESULT_ok) {
        // Increase object ref counts if storing them!
        Py_INCREF(context->py_callback);
        Py_INCREF(context->py_context);
        registered_callbacks_.push_back(context);
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
    scs_log = version_params->common.log;
    scs_register_for_channel = version_params->register_for_channel;
    log_loader("Initializing");

    // Set up path so the py file can be found
    std::string pwd = getenv("PWD");
    std::string plugin_dir = pwd + "/plugins";
    setenv("PYTHONPATH", plugin_dir.c_str(), 1);
    
    PyImport_AppendInittab("telemetry", &pymod::create);
    
    Py_Initialize();
    PyEval_InitThreads();

    std::string python_module_name = "pyets2_telemetry";
    PyObject *py_module_name = PyUnicode_DecodeFSDefaultAndSize(python_module_name.c_str(), python_module_name.size());
    if (py_module_name == NULL) {
        log_loader("Could not create python filename string");
        Py_Finalize();
        return SCS_RESULT_generic_error;
    }
    
    log_loader("Importing python module \"%s\"", python_module_name.c_str());
    // TODO: relative import. Use "level"
    py_module = PyImport_Import(py_module_name);
    Py_DECREF(py_module_name);
    if (py_module == NULL) {
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

    py_thread_state_ = PyEval_SaveThread();

    return SCS_RESULT_ok;
}

SCSAPI_VOID scs_telemetry_shutdown() {
    PyEval_RestoreThread(py_thread_state_);

    log_loader("Call telemetry_shutdown");
    pyhelp::try_call_function("telemetry_shutdown");

    log_loader("Unloading");

    // Not doing DECREF of the callback Python objects, but
    // should be fine since we are destroying Python anyway
    registered_callbacks_.clear();
    
    // TODO: XDECREF can handle NULL. Use it to have dumber exit code
    Py_DECREF(py_module);
    Py_Finalize();

    log_loader("Unloaded");
}
