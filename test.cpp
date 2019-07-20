#include <iostream>

#include <unistd.h>

#include "scssdk_telemetry.h"
#include "eurotrucks2/scssdk_eut2.h"
#include "eurotrucks2/scssdk_telemetry_eut2.h"
#include "amtrucks/scssdk_ats.h"
#include "amtrucks/scssdk_telemetry_ats.h"

//static SCSAPI_VOID_FPTR
static void log(const scs_log_type_t type, const scs_string_t message) {
    std::cout << "LOG: " << message << std::endl;
}

static std::string cb_name_;
static scs_u32_t cb_index_;
static scs_value_type_t cb_type_;
static scs_telemetry_channel_callback_t cb_callback_;
static scs_context_t cb_context_;

static SCSAPI_RESULT register_for_channel(const scs_string_t name, const scs_u32_t index, const scs_value_type_t type, const scs_u32_t flags, const scs_telemetry_channel_callback_t callback, const scs_context_t context) {
    if (type != SCS_VALUE_TYPE_u32) {
        return 0;
    }
    cb_name_ = name;
    cb_index_ = index;
    cb_type_ = type;
    cb_callback_ = callback;
    cb_context_ = context;
    return 0;
}

static void load() {
    scs_telemetry_init_params_v100_t params;
    params.common.game_name = "game";
    params.common.game_id = "id";
    params.common.game_version = 2;
    params.common.log = log;
    params.register_for_channel = register_for_channel;
    SCSAPI_RESULT result = scs_telemetry_init(SCS_TELEMETRY_VERSION_1_01, &params);

    if (cb_callback_ != nullptr) {
        if (cb_type_ == SCS_VALUE_TYPE_u32) {
            std::cout << "Calling callback" << std::endl;
            scs_value_t value;
            value.type = cb_type_;
            value.value_u32.value = 123;
            cb_callback_(cb_name_.c_str(), cb_index_, &value, cb_context_);
            cb_callback_(cb_name_.c_str(), cb_index_, &value, cb_context_);
        }
    }
    
    if (result == SCS_RESULT_ok) {
        std::cout << "RUNNING. Press enter to continue."; std::cin.get();
//        sleep(10);
        scs_telemetry_shutdown();
    }
}

int main(int argc, char *argv[]) {
    load();
    load();
    return 0;
}
