#include "pyhelp.hpp"

#include "log.hpp"

namespace pyhelp {

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

bool try_call_function(pyhelp::PyObjRef &py_module, const char *name) {
    return try_call_function(py_module, name, "()");
}

PyObjRef::PyObjRef() : py_obj_(nullptr) {
}
    
PyObjRef::PyObjRef(PyObject *py_obj) : py_obj_(py_obj) {
    inc_ref();
}

PyObjRef::PyObjRef(const PyObjRef &other) : py_obj_(other.py_obj_) {
    inc_ref();
}

PyObjRef::PyObjRef(PyObjRef &&other) : py_obj_(other.py_obj_) {
    other.py_obj_ = nullptr;
}

PyObjRef &PyObjRef::operator=(const PyObjRef &other) {
    if (&other != this) {
        py_obj_ = other.py_obj_;
        inc_ref();
    }
    return *this;
}

PyObjRef::~PyObjRef() {
    dec_ref();
}

PyObject *PyObjRef::get() {
    return py_obj_;
}

void PyObjRef::set(PyObject *py_obj) {
    if (py_obj != py_obj_) {
        dec_ref();
        py_obj_ = py_obj;
        inc_ref();
    }
}

void PyObjRef::reset() {
    set(nullptr);
}

void PyObjRef::inc_ref() {
    if (py_obj_ != nullptr) {
        Py_INCREF(py_obj_);
    }
}

void PyObjRef::dec_ref() {
    if (py_obj_ != nullptr) {
        Py_DECREF(py_obj_);
    }
}

}
