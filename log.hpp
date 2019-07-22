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

#ifndef _LOG_HPP_
#define _LOG_HPP_

#include <string>

#include "scssdk_telemetry.h"

void log_set_scs_log(scs_log_t scs_log);
    
// Log messages with loader prefix
void log_loader(const char *format, ...)
    __attribute__ ((format (printf, 1, 2)));

// Log messages with Python prefix
void log_py(const char *message);

void log(const std::string &prefix, const char *format, va_list ap);
void log(const std::string &prefix, const char *format, ...)
    __attribute__ ((format (printf, 2, 3)));

#endif
