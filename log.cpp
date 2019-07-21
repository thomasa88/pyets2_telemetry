#include "log.hpp"

#include <cstdarg>

static scs_log_t scs_log_;

void log_set_scs_log(scs_log_t scs_log) {
    scs_log_ = scs_log;
}

void log(const std::string &prefix, const char *format, va_list ap) {
    if (scs_log_ == nullptr) {
        // No log function
        return;
    }
    std::string buf(prefix);
    buf.resize(256);
    vsnprintf(buf.data() + prefix.size(), buf.size() - prefix.size(), format, ap);
    scs_log_(SCS_LOG_TYPE_message, buf.c_str());
}

void log(const std::string &prefix, const char *format, ...) {
    va_list ap;
    va_start(ap, format);
    log(prefix, format, ap);
    va_end(ap);
}

void log_loader(const char *format, ...) {
    const std::string prefix = "PyETS2 Telemetry Loader: ";
    va_list ap;
    va_start(ap, format);
    log(prefix, format, ap);
    va_end(ap);
}

void log_py(const char *message) {
    const std::string prefix = "PyETS2 Telemetry: ";
    log(prefix, "%s", message);
}
