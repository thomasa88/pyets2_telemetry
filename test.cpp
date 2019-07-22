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

static std::string channel_cb_name_;
static scs_u32_t channel_cb_index_;
static scs_value_type_t channel_cb_type_;
static scs_telemetry_channel_callback_t channel_cb_callback_;
static scs_context_t channel_cb_context_;

static scs_event_t event_cb_event_;
static scs_telemetry_event_callback_t event_cb_callback_;
static scs_context_t event_cb_context_;

static SCSAPI_RESULT register_for_channel(const scs_string_t name, const scs_u32_t index, const scs_value_type_t type, const scs_u32_t flags, const scs_telemetry_channel_callback_t callback, const scs_context_t context) {
    if (type != SCS_VALUE_TYPE_u32) {
        return 0;
    }
    channel_cb_name_ = name;
    channel_cb_index_ = index;
    channel_cb_type_ = type;
    channel_cb_callback_ = callback;
    channel_cb_context_ = context;
    return 0;
}

static SCSAPI_RESULT register_for_event(const scs_event_t event, const scs_telemetry_event_callback_t callback, const scs_context_t context) {
    if (event != SCS_TELEMETRY_EVENT_configuration) {
        return 0;
    }
    event_cb_event_ = event;
    event_cb_callback_ = callback;
    event_cb_context_ = context;
    return 0;
}

static void load() {
    scs_telemetry_init_params_v100_t params;
    params.common.game_name = "game";
    params.common.game_id = "id";
    params.common.game_version = 2;
    params.common.log = log;
    params.register_for_channel = register_for_channel;
    params.register_for_event = register_for_event;
    SCSAPI_RESULT result = scs_telemetry_init(SCS_TELEMETRY_VERSION_1_01, &params);

    if (channel_cb_callback_ != nullptr) {
        if (channel_cb_type_ == SCS_VALUE_TYPE_u32) {
            std::cout << "Calling channel callback" << std::endl;
            scs_value_t value;
            value.type = channel_cb_type_;
            value.value_u32.value = 123;
            channel_cb_callback_(channel_cb_name_.c_str(), channel_cb_index_, &value, channel_cb_context_);
            channel_cb_callback_(channel_cb_name_.c_str(), channel_cb_index_, &value, channel_cb_context_);
        }
    }

    if (event_cb_callback_ != nullptr) {
        if (event_cb_event_ == SCS_TELEMETRY_EVENT_configuration) {
            std::cout << "Calling event callback" << std::endl;
            scs_telemetry_configuration_t config;
            config.id = "config";
            scs_named_value_t attributes[3];
            config.attributes = attributes;
            attributes[0].name = "attr0";
            attributes[0].index = 0;
            attributes[0].value.type = SCS_VALUE_TYPE_u32;
            attributes[0].value.value_u32.value = 5;
            attributes[1].name = "attr1";
            attributes[1].index = 1;
            attributes[1].value.type = SCS_VALUE_TYPE_float;
            attributes[1].value.value_float.value = 6.3;
            attributes[2].name = nullptr;
            void *event_info = static_cast<void*>(&config);
            event_cb_callback_(event_cb_event_, event_info, event_cb_context_);
            event_cb_callback_(event_cb_event_, event_info, event_cb_context_);
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
