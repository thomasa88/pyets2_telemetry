#
# Copyright 2019 Thomas Axelsson <thomasa88@gmail.com>
#
# This file is part of pyets2_telemetry.
#
# pyets2_telemetry is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pyets2_telemetry is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyets2_telemetry.  If not, see <https://www.gnu.org/licenses/>.
#

import importlib
import logging
import pkgutil
from pyets2lib.scsdefs import *
import pyets2lib.scshelpers

import _telemetry

class TelemetryLogHandler(logging.Handler):
    def emit(self, record):
        _telemetry.log(self.format(record))

logging.basicConfig(level=logging.INFO, handlers=(TelemetryLogHandler(),))

logger_ = logging.getLogger(__name__)
modules_ = []

class CallbackInfo(object):
    def __init__(self):
        self.listeners = []

class scs_telemetry_init_params_v100_t(object):
    def __init__(self, common):
        self.common = common
    
    def register_for_event(self, event, callback, context=None):
        '''
        Register for listening on an event.

        The callback should be declared as:
        def event_cb(event, event_info, context)
        '''
        loader_context = event
        ret = _telemetry.register_for_event(event.id, event_cb, loader_context)
        if ret != SCS_RESULT_ok:
            raise Exception("Failed to register to event \"%s\": %d" %
                            (event.name, ret))

        if not hasattr(event, '_loader_info'):
            event._loader_info = CallbackInfo()
        event._loader_info.listeners.append((callback, context))

    # def unregister_from_event(event, callback)

    def register_for_channel(self, channel, callback, index=None, context=None):
        '''
        Register for listening on a channel.

        The callback should be declared as:
        def channel_cb(channel, index, value, context)
        '''
        if index is None:
            scs_index = SCS_U32_NIL
        else:
            scs_index = index
        loader_context = channel
        ret = _telemetry.register_for_channel(channel.name,
                                              scs_index,
                                              channel.type,
                                              SCS_TELEMETRY_CHANNEL_FLAG_none,
                                              channel_cb,
                                              loader_context)
        if ret != SCS_RESULT_ok:
            raise Exception("Failed to register to channel \"%s\": %d" %
                            (channel.name, ret))

        if not hasattr(channel, '_loader_info'):
            channel._loader_info = CallbackInfo()
        channel._loader_info.listeners.append((callback, context))

    # def unregister_from_channel(channel, index=None, callback)

class scs_sdk_init_params_v100_t(object):
    def __init__(self, game_name, game_id, game_version, logger):
        self.game_name = game_name
        self.game_id = game_id
        self.game_version = game_version
        self.logger = logger
    
def channel_cb(name, index, value, loader_context):
    channel = loader_context
    for callback, context in channel._loader_info.listeners:
        try_call_method(None, callback, channel, index, value, context)

def event_cb(event_id, event_info, loader_context):
    event = loader_context
    for callback, context in event._loader_info.listeners:
        try_call_method(None, callback, event, event_info, context)

def telemetry_init(version, game_name, game_id, game_version):
    for info in pkgutil.iter_modules(['plugins/python']):
        if info.ispkg:
            if info.name == __package__:
                # Skip ourselves
                continue
            logger_.info("Loading Python plug-in \"%s\"" % info.name)
            module = try_call_method(logging.getLogger(info.name),
                                     importlib.import_module, info.name)[1]
            if not module:
                continue
            modules_.append(module)
            
            common = scs_sdk_init_params_v100_t(game_name, game_id, game_version,
                                                logging.getLogger(info.name))
            init_params = scs_telemetry_init_params_v100_t(common)
            try_call_method(None, module.telemetry_init, version, init_params)

def telemetry_shutdown():
    for module in modules_:
        try_call_method(None, module.telemetry_shutdown)

def try_call_method(logger, method, *args, **kwargs):
    ret = None
    try:
        ret = method(*args, **kwargs)
    except Exception as e:
        if not logger:
            logger = logging.getLogger(method.__module__)
        pyets2lib.scshelpers.log_exception(logger, e)
        return (False, ret)
    return (True, ret)
