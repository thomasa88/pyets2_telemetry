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

// Python call helpers

#ifndef _PYHELP_HPP_
#define _PYHELP_HPP_

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "log.hpp"

namespace pyhelp {

// Handles reference counting of PyObject*
class PyObjRef {
public:
    PyObjRef();    
    explicit PyObjRef(PyObject *py_obj);
    PyObjRef(const PyObjRef &other);
    PyObjRef(PyObjRef &&other);
    PyObjRef &operator=(const PyObjRef &other);
    ~PyObjRef();

    PyObject *get();
    void set(PyObject *py_obj);
    void reset();
private:
    void inc_ref();
    void dec_ref();

    PyObject *py_obj_;
};

// Equivalent to PyErr_Print()
void log_and_clear_py_err();

template <class ... Args>
bool try_call_function(PyObject *py_func,
                       const char *arg_format,
                       Args... args) {
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
bool try_call_function(pyhelp::PyObjRef &py_module,
                       const char *name,
                       const char *arg_format,
                       Args... args) {
    PyObjRef py_func(PyObject_GetAttrString(py_module.get(), name));
    bool ok = try_call_function(py_func.get(), arg_format, args...);
    if (!ok) {
        log_loader("Calling function %s failed", name);
    }
    return ok;
}

bool try_call_function(pyhelp::PyObjRef &py_module, const char *name);

}

#endif
