//
// Copyright 2019 Thomas Axelsson <thomasa88@gmail.com>
//
// This file is part of pyets2_telemetry.
//
// pyets2_telemetry is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// pyets2_telemetry is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with pyets2_telemetry.  If not, see <https://www.gnu.org/licenses/>.
//

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

#include "pyhelp.hpp"
#include "log.hpp"

static scs_telemetry_init_params_v101_t scs_params_;
static pyhelp::PyObjRef py_module_;
static PyThreadState *py_thread_state_ = nullptr;

struct cb_context {
    pyhelp::PyObjRef py_callback;
    pyhelp::PyObjRef py_context;
};
static std::vector<cb_context> registered_channels_;
static std::vector<cb_context> registered_events_;


// telemetry Python module

template <class T>
static pyhelp::PyObjRef create_py_vector(const T &scs_vector) {
    pyhelp::PyObjRef py_dict(PyDict_New());
    PyDict_SetItemString(py_dict.get(), "x",
                         PyFloat_FromDouble(scs_vector.x));
    PyDict_SetItemString(py_dict.get(), "y",
                         PyFloat_FromDouble(scs_vector.y));
    PyDict_SetItemString(py_dict.get(), "z",
                         PyFloat_FromDouble(scs_vector.z));
    return py_dict;
}

static pyhelp::PyObjRef create_py_euler(const scs_value_euler_t &euler) {
    pyhelp::PyObjRef py_dict(PyDict_New());
    PyDict_SetItemString(py_dict.get(), "heading",
                         PyFloat_FromDouble(euler.heading));
    PyDict_SetItemString(py_dict.get(), "pitch",
                         PyFloat_FromDouble(euler.pitch));
    PyDict_SetItemString(py_dict.get(), "roll",
                         PyFloat_FromDouble(euler.roll));
    return py_dict;
}

// Returns empty pyhelp::PyObjRef on error
static pyhelp::PyObjRef create_py_value(const scs_value_t *value) {
    pyhelp::PyObjRef py_value;
    if (value == nullptr) {
        return py_value;
    }
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
        case SCS_VALUE_TYPE_fvector:
            py_value = create_py_vector(value->value_fvector);
            break;
        case SCS_VALUE_TYPE_dvector:
            py_value = create_py_vector(value->value_dvector);
            break;
        case SCS_VALUE_TYPE_euler:
            py_value = create_py_euler(value->value_euler);
            break;
        case SCS_VALUE_TYPE_fplacement:
            py_value.set(PyDict_New());
            PyDict_SetItemString(py_value.get(), "position",
                                 create_py_vector(
                                     value->value_fplacement.position).get());
            PyDict_SetItemString(py_value.get(), "orientation",
                                 create_py_euler(
                                     value->value_fplacement.orientation).get());
            break;
        case SCS_VALUE_TYPE_dplacement:
            py_value.set(PyDict_New());
            PyDict_SetItemString(py_value.get(), "position",
                                 create_py_vector(
                                     value->value_fplacement.position).get());
            PyDict_SetItemString(py_value.get(), "orientation",
                                 create_py_euler(
                                     value->value_fplacement.orientation).get());
            break;
        case SCS_VALUE_TYPE_string:
            py_value.set(PyUnicode_FromString(value->value_string.value));
            break;
        default:
            log_loader("Cannot convert SCS type: %u", value->type);
    }
    return py_value;
}

SCSAPI_VOID telemetry_channel_cb(const scs_string_t name,
                                 const scs_u32_t index,
                                 const scs_value_t *const value,
                                 const scs_context_t context) {
    int context_index = reinterpret_cast<intptr_t>(context);
    if (context_index >= static_cast<ssize_t>(registered_channels_.size())) {
        log_loader("ERROR! Channel context_index=%d > size()=%zu. Ignoring callback.",
                   context_index, registered_channels_.size());
        return;
    }
    cb_context &context_val = registered_channels_[context_index];
    
    PyEval_RestoreThread(py_thread_state_);

    { // Make sure no pyhelp::PyObjRef ref counting happens after PyEval_SaveThread()
        // value might be NULL if user has set SCS_TELEMETRY_CHANNEL_FLAG_no_value
        pyhelp::PyObjRef py_value(create_py_value(value));
        if (py_value.get() == nullptr) {
            py_value.set(Py_None);
        }
        pyhelp::try_call_function(context_val.py_callback.get(),
                                  "sIOO", name, index,
                                  py_value.get(), context_val.py_context.get());
    }
    py_thread_state_ = PyEval_SaveThread();
}

SCSAPI_VOID telemetry_event_cb(const scs_event_t event,
                               const void *const event_info,
                               const scs_context_t context) {
    int context_index = reinterpret_cast<intptr_t>(context);
    if (context_index >= static_cast<ssize_t>(registered_events_.size())) {
        log_loader("ERROR! Event context_index=%d > size()=%zu. Ignoring callback.",
                   context_index, registered_events_.size());
        return;
    }
    cb_context &context_val = registered_events_[context_index];
    
    PyEval_RestoreThread(py_thread_state_);

    { // Make sure no pyhelp::PyObjRef ref counting happens after PyEval_SaveThread()
        pyhelp::PyObjRef py_value(Py_None);

        // TODO: Use custom types (PyType) instead of dicts? Config and gameplay
        // events should not happen very often?
        switch (event) {
            // TODO: Implement all event types
            // case SCS_TELEMETRY_EVENT_frame_start:
            //     break;
            // case SCS_TELEMETRY_EVENT_frame_end:
            //     break;
            case SCS_TELEMETRY_EVENT_paused:
                // No value
                break;
            case SCS_TELEMETRY_EVENT_started:
                // No value
                break;
            case SCS_TELEMETRY_EVENT_gameplay:
                // Intentional fall-through. The struct layouts are the same.
            case SCS_TELEMETRY_EVENT_configuration:
                auto config = static_cast<const scs_telemetry_configuration_t *const>(event_info);
                py_value.set(PyDict_New());
                PyDict_SetItemString(py_value.get(), "id",
                                     PyUnicode_FromString(config->id));
                pyhelp::PyObjRef py_attr_list(PyList_New(0));
                PyDict_SetItemString(py_value.get(), "attributes",
                                     py_attr_list.get());
                const scs_named_value_t *current_attr = config->attributes;
                for (; current_attr->name != nullptr; ++current_attr) {
                    pyhelp::PyObjRef py_attr_value(create_py_value(&current_attr->value));
                    if (py_attr_value.get() == nullptr) {
                        py_attr_value.set(Py_None);
                    }

                    PyObject *py_index = Py_None;
                    if (current_attr->index != SCS_U32_NIL) {
                        py_index = PyLong_FromUnsignedLong(current_attr->index);
                    }
 
                    PyObject *py_attr_tuple = PyTuple_Pack(
                        3,
                        PyUnicode_FromString(current_attr->name),
                        py_index,
                        py_attr_value.get());

                    PyList_Append(py_attr_list.get(), py_attr_tuple);
                }
                break;
                //default:
                // Keep None-value
        }
        pyhelp::try_call_function(context_val.py_callback.get(),
                                  "IOO", event, py_value.get(),
                                  context_val.py_context.get());
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
    auto context_it = registered_channels_.emplace(registered_channels_.end(),
                                                std::move(context));
    // Cannot store pointer to element in the vector, as the vector
    // reallocates when it grows. Using index instead.
    intptr_t context_index = context_it - registered_channels_.begin();
    SCSAPI_RESULT register_ret =
        scs_params_.register_for_channel(name, index, type, flags,
                                         telemetry_channel_cb,
                                         reinterpret_cast<void*>(context_index));
    if (register_ret != SCS_RESULT_ok) {
        registered_channels_.pop_back(); 
    }
    return PyLong_FromLong(register_ret);
}

static PyObject *register_for_event(PyObject *self, PyObject *args) {
    scs_event_t event = 0;
    PyObject *py_callback;
    PyObject *py_context;
    if (!PyArg_ParseTuple(args, "IOO", &event, &py_callback,
                          &py_context)) {
        return nullptr;
    }
    cb_context context;
    context.py_callback.set(py_callback);
    context.py_context.set(py_context);
    auto context_it = registered_events_.emplace(registered_events_.end(),
                                                 std::move(context));
    // Cannot store pointer to element in the vector, as the vector
    // reallocates when it grows. Using index instead.
    intptr_t context_index = context_it - registered_events_.begin();
    SCSAPI_RESULT register_ret =
        scs_params_.register_for_event(event, telemetry_event_cb,
                                       reinterpret_cast<void*>(context_index));
    if (register_ret != SCS_RESULT_ok) {
        registered_events_.pop_back(); 
    }
    return PyLong_FromLong(register_ret);
}

static PyMethodDef methods[] = {
    {"log", log, METH_O,
     "Log a message to ETS2 developer console."},
    {"register_for_channel", register_for_channel, METH_VARARGS,
     "Registers callback to be called with value of specified telemetry channel."},
    {"register_for_event", register_for_event, METH_VARARGS,
     "Registers callback to be called when specified event happens."},
    {NULL, NULL, 0, NULL}
};

static PyModuleDef module = {
    PyModuleDef_HEAD_INIT, "_telemetry", NULL, -1, methods,
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
    const scs_telemetry_init_params_v101_t *version_params = static_cast<const scs_telemetry_init_params_v101_t *>(params);
    scs_params_ = *version_params;

    log_set_scs_log(scs_params_.common.log);

    log_loader("Initializing");

    // Set up path so the py file can be found
    // Using Py_SetPath overwrites all Python paths, making next Py_Initialize
    // fail, so using the simpler PYTHONPATH instead.
    std::string pwd = getenv("PWD");
    std::string plugin_dir = pwd + "/plugins/python";
    setenv("PYTHONPATH", plugin_dir.c_str(), 1);
    
    PyImport_AppendInittab("_telemetry", &pymod::create);
    
    Py_InitializeEx(0);
    PyEval_InitThreads();

    { // Make sure no pyhelp::PyObjRef ref counting happens after PyEval_SaveThread()
        std::string python_module_name = "pyets2lib.loader";
        pyhelp::PyObjRef py_module_name(PyUnicode_DecodeFSDefaultAndSize(
                                    python_module_name.c_str(),
                                    python_module_name.size()));
        if (py_module_name.get() == nullptr) {
            log_loader("Could not create python filename string");
            Py_Finalize();
            return SCS_RESULT_generic_error;
        }
    
        log_loader("Loading Python framework");
        // TODO: relative import. Use "level"
        py_module_.set(PyImport_Import(py_module_name.get()));
        if (py_module_.get() == nullptr) {
            log_loader("Could not import python module");
            pyhelp::log_and_clear_py_err();
            Py_Finalize();
            return SCS_RESULT_generic_error;
        }
        log_loader("Python framework loaded");

        pyhelp::try_call_function(py_module_, "telemetry_init", "IssI",
                                  version,
                                  scs_params_.common.game_name,
                                  scs_params_.common.game_id,
                                  scs_params_.common.game_version);
    }

    py_thread_state_ = PyEval_SaveThread();

    return SCS_RESULT_ok;
}

SCSAPI_VOID scs_telemetry_shutdown() {
    PyEval_RestoreThread(py_thread_state_);

    log_loader("Call telemetry_shutdown");
    pyhelp::try_call_function(py_module_, "telemetry_shutdown");

    log_loader("Unloading");

    registered_channels_.clear();
    registered_events_.clear();
    py_module_.reset();

    // All pyhelp::PyObjRef must be destroyed/reset before this point!
    // TODO: Class?
    Py_Finalize();

    py_thread_state_ = nullptr;

    log_loader("Unloaded");
    log_set_scs_log(nullptr);
}
