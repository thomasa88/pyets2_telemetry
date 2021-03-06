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
