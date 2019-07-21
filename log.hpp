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
