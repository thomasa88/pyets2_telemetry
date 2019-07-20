import logging
import threading
from datetime import datetime, timedelta

import telemetry
import web_server
from scs_defs import *

# From ETS2 Telemetry Server
TELEMETRY_PLUGIN_VERSION = '4'

GAME_TIME_BASE = datetime(1, 1, 1)

server_ = None
server_thread_ = None
game_time_ = GAME_TIME_BASE
delivery_time_ = GAME_TIME_BASE

# NOTE: new_data indicator only works well with 1 client.
# Need to track connection/session ids to handle multiple clients
# and call notify_all().
shared_data_ = {
    'condition': threading.Condition(),
    'telemetry_data': {},
    'new_data': False
}

# Only call these functions when shared_data is locked!
def set_shared_value(json0, json1, value):
    shared_data_['telemetry_data'][json0][json1] = value

def shared_data_notify():
    shared_data_['new_data'] = True
    shared_data_['condition'].notify()

# Setting up logging, so other threads can log to the game console
class TelemetryLogHandler(logging.Handler):
    # Is locking (thread safety) included in logging.Handler?
    def emit(self, record):
        telemetry.log(self.format(record))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(TelemetryLogHandler())

def telemetry_init(version, game_name, game_id, game_version):
    init_shared_data()
    shared_data_['telemetry_data']['game']['gameName'] = game_id.upper().replace('EUT2', 'ETS2')
    shared_data_['telemetry_data']['game']['version'] = game_name.split(' ')[-1]

    telemetry.register_for_event(SCS_TELEMETRY_EVENT_configuration, event_cb, None)
    for channel in SCS_CHANNELS:
        if not hasattr(channel, 'json_path'):
            continue
        if channel.indexed:
            index = 0
        else:
            index = None
        register_for_channel(channel, channel.internal_id, index)
    start_server()

def register_for_channel(channel, context, index=None):
    if index is None:
        scs_index = SCS_U32_NIL
    else:
        scs_index = index
    ret = telemetry.register_for_channel(channel.name,
                                         scs_index,
                                         channel.type,
                                         SCS_TELEMETRY_CHANNEL_FLAG_none,
                                         channel_cb, context)
    if ret != SCS_RESULT_ok:
        raise Exception("Failed to register to channel \"%s\": %d" %
                        (channel.name, ret))

def channel_cb(name, index, value, context):
    global game_time_, delivery_time_    
    
    channel = SCS_CHANNELS[context]

    with shared_data_['condition']:
        # # Optimize this?
        if channel == SCS_TELEMETRY_CHANNEL_game_time:
            game_time_ = GAME_TIME_BASE + timedelta(minutes=value)
            if game_time_ > delivery_time_:
                # Passed the deadline
                remaining_time = timedelta(0)
            else:
                remaining_time = delivery_time_ - game_time_
            set_shared_value('job', 'remainingTime',
                             json_time(
                                 GAME_TIME_BASE + remaining_time))
        elif channel == SCS_TELEMETRY_TRUCK_CHANNEL_dashboard_backlight:
            set_shared_value('truck', 'lightsDashboardOn', value > 0)
        elif channel == SCS_TELEMETRY_TRUCK_CHANNEL_cruise_control:
            set_shared_value('truck', 'cruiseControlOn', value > 0)

        if hasattr(channel, 'conv_func'):
            value = channel.conv_func(value)

        if isinstance(value, datetime):
            value = json_time(value)

        set_shared_value(channel.json_path[0], channel.json_path[1], value)
        shared_data_notify()

def event_cb(event, event_info, context):
    global game_time_, delivery_time_
    if event == SCS_TELEMETRY_EVENT_configuration:
        with shared_data_['condition']:
            event_map = CONFIG_EVENT_MAP.get(event_info['id'])
            if event_map is not None:
                for name, index, value in event_info['attributes']:
                    json_path = event_map.get(name)
                    if json_path is not None:
                        save_value = value
                        if len(json_path) > 2:
                            conv_func = json_path[2]
                            value = conv_func(value)
                            if name == SCS_TELEMETRY_CONFIG_ATTRIBUTE_delivery_time:
                                # Remaining time will change as game time
                                # progresses, so let's save delivery time
                                # and calculate remaining time when game
                                # time changes.
                                delivery_time_ = value
                            if isinstance(value, datetime):
                                value = json_time(value)
                                
                        set_shared_value(json_path[0], json_path[1], value)
            shared_data_notify()
    elif event == SCS_TELEMETRY_EVENT_started:
        with shared_data_['condition']:
            set_value('game', 'paused', False)
            shared_data_notify()
    elif event == SCS_TELEMETRY_EVENT_paused:
        with shared_data_['condition']:
            set_value('game', 'paused', True)
            shared_data_notify()
        
def start_server():
    global server_, server_thread_
    server_ = web_server.SignalrHttpServer(shared_data_)

    # Using Python Threading for now. Switch to Multiprocessing if this
    # becomes a performance problem. This will affect logging and data sharing.
    server_thread_ = threading.Thread(target=server_.serve_forever)
    server_thread_.name = "signalr server"
    server_thread_.start()

    telemetry.log("Started server on port %u" % server_.PORT_NUMBER)

def telemetry_shutdown():
    logging.info("Shutting down")
    if server_:
        stop_server()
    telemetry.log("bye")

def stop_server():
    server_.shutdown()
    server_thread_.join()
    server_.server_close()
    telemetry.log("Stopped server")

def init_shared_data():
    shared_data_['new_data'] = True
    shared_data_['telemetry_data'] = {
        'game': {
            'connected': True,
            'paused': False,
            'time': '0001-01-08T21: 09: 00Z',
            'timeScale': 19.0,
            'nextRestStopTime': '0001-01-01T10: 11: 00Z',
            'version': '1.10',
            'telemetryPluginVersion': TELEMETRY_PLUGIN_VERSION
        },
        'truck': {
            'id': 'man', # Probably config for truck! with correct config attribute!
            'make': 'MAN', #?
            'model': 'TGX', #?
            'speed': 0.0,
            'cruiseControlSpeed': 0.0,
            'cruiseControlOn': False,
            'odometer': 0.0,
            'gear': 1,
            'displayedGear': 1,
            'forwardGears': 12,
            'reverseGears': 1,
            'shifterType': 'arcade',
            'engineRpm': 0.0,
            'engineRpmMax': 2500.0,
            'fuel': 0.0,
            'fuelCapacity': 700.0,
            'fuelAverageConsumption': 0.1,
            'fuelWarningFactor': 0.15,
            'fuelWarningOn': False,
            'wearEngine': 0.0,
            'wearTransmission': 0.0,
            'wearCabin': 0.0,
            'wearChassis': 0.0,
            'wearWheels': 0.0,
            'userSteer': 0.0, # wheel + input steering. scale wheel *4
            'userThrottle': 1.0, # wheel + input
            'userBrake': 0.0,
            'userClutch': 0.0,
            'gameSteer': 0.0,
            'gameThrottle': 1.0,
            'gameBrake': 0.0,
            'gameClutch': 0.0,
            'shifterSlot': 0,
            'engineOn': False,
            'electricOn': False,
            'wipersOn': False,
            'retarderBrake': 0,
            'retarderStepCount': 3,
            'parkBrakeOn': False,
            'motorBrakeOn': False,
            'brakeTemperature': 0.0,
            'adblue': 0.0,
            'adblueCapacity': 0.0,
            'adblueAverageConsumption': 0.0,
            'adblueWarningOn': False,
            'airPressure': 0.0,
            'airPressureWarningOn': False,
            'airPressureWarningValue': 65.0,
            'airPressureEmergencyOn': False,
            'airPressureEmergencyValue': 30.0,
            'oilTemperature': 0.0,
            'oilPressure': 0.0,
            'oilPressureWarningOn': False,
            'oilPressureWarningValue': 10.0,
            'waterTemperature': 0.0,
            'waterTemperatureWarningOn': False,
            'waterTemperatureWarningValue': 105.0,
            'batteryVoltage': 24.0,
            'batteryVoltageWarningOn': False,
            'batteryVoltageWarningValue': 22.0,
            'lightsDashboardValue': 1.0,
            'lightsDashboardOn': False,
            'blinkerLeftActive': False,
            'blinkerRightActive': False,
            'blinkerLeftOn': False,
            'blinkerRightOn': False,
            'lightsParkingOn': False,
            'lightsBeamLowOn': False,
            'lightsBeamHighOn': False,
            'lightsAuxFrontOn': False,
            'lightsAuxRoofOn': False,
            'lightsBeaconOn': False,
            'lightsBrakeOn': False,
            'lightsReverseOn': False,
            'placement': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'heading': 0.0,
                'pitch': 0.0,
                'roll': 0.0,
            },
            'acceleration': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
            },
            'head': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
            },
            'cabin': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
            },
            'hook': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
            }
        },
        'trailer': {
            'attached': False,
            'id': 'derrick', #?
            'name': 'derrick', #?
            'mass': 22000.0,
            'wear': 0.0,
            'placement': {
                'x': 0.0,
                'y': 0.0,
                'z': 0.0,
                'heading': 0.0,
                'pitch': 0.0,
                'roll': 0.0,
            }
        },
        'job': {
            'income': 0,
            'deadlineTime': '0001-01-09T03: 34: 00Z',
            'remainingTime': '0001-01-01T06: 25: 00Z',
            'sourceCity': '<sourceCity>',
            'sourceCompany': '<sourceCompany>',
            'destinationCity': '<destinationCity>',
            'destinationCompany': '<destinationCompany>'
        },
        'navigation': {
            'estimatedTime': '0001-01-01T03: 01: 40Z',
            'estimatedDistance': 0,
            'speedLimit': 90
        }
    }

    shared_data_['telemetry_data'] = {
        'game': {
            'connected': True,
            'paused': False,
            'time': 'NO VALUE',
            'timeScale': 13.37,
            'nextRestStopTime': 'NO VALUE',
            'version': 'NO VALUE',
            'telemetryPluginVersion': TELEMETRY_PLUGIN_VERSION
        },
        'truck': {
            'id': 'NO VALUE', # Probably config for truck! with correct config attribute!
            'make': 'NO VALUE', #?
            'model': 'NO VALUE', #?
            'speed': 13.37,
            'cruiseControlSpeed': 13.37,
            'cruiseControlOn': False,
            'odometer': 13.37,
            'gear': 99,
            'displayedGear': 99,
            'forwardGears': 99,
            'reverseGears': 99,
            'shifterType': 'NO VALUE',
            'engineRpm': 13.37,
            'engineRpmMax': 13.37,
            'fuel': 13.37,
            'fuelCapacity': 13.37,
            'fuelAverageConsumption': 13.37,
            'fuelWarningFactor': 13.37,
            'fuelWarningOn': False,
            'wearEngine': 13.37,
            'wearTransmission': 13.37,
            'wearCabin': 13.37,
            'wearChassis': 13.37,
            'wearWheels': 13.37,
            'userSteer': 13.37, # wheel + input steering. scale wheel *4
            'userThrottle': 13.37, # wheel + input
            'userBrake': 13.37,
            'userClutch': 13.37,
            'gameSteer': 13.37,
            'gameThrottle': 13.37,
            'gameBrake': 13.37,
            'gameClutch': 13.37,
            'shifterSlot': 99,
            'engineOn': False,
            'electricOn': False,
            'wipersOn': False,
            'retarderBrake': 99,
            'retarderStepCount': 99,
            'parkBrakeOn': False,
            'motorBrakeOn': False,
            'brakeTemperature': 13.37,
            'adblue': 13.37,
            'adblueCapacity': 13.37,
            'adblueAverageConsumption': 13.37,
            'adblueWarningOn': False,
            'airPressure': 13.37,
            'airPressureWarningOn': False,
            'airPressureWarningValue': 13.37,
            'airPressureEmergencyOn': False,
            'airPressureEmergencyValue': 13.37,
            'oilTemperature': 13.37,
            'oilPressure': 13.37,
            'oilPressureWarningOn': False,
            'oilPressureWarningValue': 13.37,
            'waterTemperature': 13.37,
            'waterTemperatureWarningOn': False,
            'waterTemperatureWarningValue': 13.37,
            'batteryVoltage': 13.37,
            'batteryVoltageWarningOn': False,
            'batteryVoltageWarningValue': 13.37,
            'lightsDashboardValue': 13.37,
            'lightsDashboardOn': False,
            'blinkerLeftActive': False,
            'blinkerRightActive': False,
            'blinkerLeftOn': False,
            'blinkerRightOn': False,
            'lightsParkingOn': False,
            'lightsBeamLowOn': False,
            'lightsBeamHighOn': False,
            'lightsAuxFrontOn': False,
            'lightsAuxRoofOn': False,
            'lightsBeaconOn': False,
            'lightsBrakeOn': False,
            'lightsReverseOn': False,
            'placement': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
                'heading': 13.37,
                'pitch': 13.37,
                'roll': 13.37,
            },
            'acceleration': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
            },
            'head': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
            },
            'cabin': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
            },
            'hook': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
            }
        },
        'trailer': {
            'attached': False,
            'id': 'NO VALUE', #?
            'name': 'NO VALUE', #?
            'mass': 13.37,
            'wear': 13.37,
            'placement': {
                'x': 13.37,
                'y': 13.37,
                'z': 13.37,
                'heading': 13.37,
                'pitch': 13.37,
                'roll': 13.37,
            }
        },
        'job': {
            'income': 99,
            'deadlineTime': 'NO VALUE',
            'remainingTime': 'NO VALUE', # delivery_time - game_time
            'sourceCity': 'NO VALUE',
            'sourceCompany': 'NO VALUE',
            'destinationCity': 'NO VALUE',
            'destinationCompany': 'NO VALUE'
        },
        'navigation': {
            'estimatedTime': 'NO VALUE',
            'estimatedDistance': 99,
            'speedLimit': 90
        }
    }

def json_time(dt):
    return dt.isoformat(timespec='seconds')+'Z'

# Value conversion functions
def mps_to_kph(mps):
    return round(3.6 * mps)

def non_zero(value):
    return value != 0

def flatten_placement(value):
    return { **(value['position']), **(value['orientation']) }
    
# JSON mapping
SCS_TELEMETRY_CHANNEL_game_time.json_path = ('game', 'time')
SCS_TELEMETRY_CHANNEL_game_time.conv_func = lambda v: game_time_
SCS_TELEMETRY_CHANNEL_local_scale.json_path = ('game', 'timeScale')
SCS_TELEMETRY_CHANNEL_next_rest_stop.json_path = ('game', 'nextRestStopTime')
SCS_TELEMETRY_CHANNEL_next_rest_stop.conv_func = lambda v: game_time_ + timedelta(minutes=v)
SCS_TELEMETRY_TRAILER_CHANNEL_connected.json_path = ('trailer', 'attached')
SCS_TELEMETRY_TRAILER_CHANNEL_wear_chassis.json_path = ('trailer', 'wear')
SCS_TELEMETRY_TRAILER_CHANNEL_world_placement.json_path = ('trailer', 'placement')
SCS_TELEMETRY_TRAILER_CHANNEL_world_placement.conv_func = flatten_placement
# Not available? Getting SCS_RESULT_not_found
#SCS_TELEMETRY_TRUCK_CHANNEL_adblue_average_consumption.json_path = ('truck', 'adblueAverageConsumption')
SCS_TELEMETRY_TRUCK_CHANNEL_adblue.json_path = ('truck', 'adblue')
SCS_TELEMETRY_TRUCK_CHANNEL_adblue_warning.json_path = ('truck', 'adblueWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_battery_voltage.json_path = ('truck', 'batteryVoltage')
SCS_TELEMETRY_TRUCK_CHANNEL_battery_voltage_warning.json_path = ('truck', 'batteryVoltageWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure_emergency.json_path = ('truck', 'airPressureEmergencyOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure.json_path = ('truck', 'airPressure')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_air_pressure_warning.json_path = ('truck', 'airPressureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_brake_temperature.json_path = ('truck', 'brakeTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_cruise_control.json_path = ('truck', 'cruiseControlSpeed')
SCS_TELEMETRY_TRUCK_CHANNEL_cruise_control.conv_func = mps_to_kph
SCS_TELEMETRY_TRUCK_CHANNEL_dashboard_backlight.json_path = ('truck', 'lightsDashboardValue')
SCS_TELEMETRY_TRUCK_CHANNEL_displayed_gear.json_path = ('truck', 'displayedGear')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_brake.json_path = ('truck', 'gameBrake')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_clutch.json_path = ('truck', 'gameClutch')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_steering.json_path = ('truck', 'gameSteer')
SCS_TELEMETRY_TRUCK_CHANNEL_effective_throttle.json_path = ('truck', 'gameThrottle')
SCS_TELEMETRY_TRUCK_CHANNEL_electric_enabled.json_path = ('truck', 'electricOn')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_enabled.json_path = ('truck', 'engineOn')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_gear.json_path = ('truck', 'gear')
SCS_TELEMETRY_TRUCK_CHANNEL_engine_rpm.json_path = ('truck', 'engineRpm')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel_average_consumption.json_path = ('truck', 'fuelAverageConsumption')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel.json_path = ('truck', 'fuel')
SCS_TELEMETRY_TRUCK_CHANNEL_fuel_warning.json_path = ('truck', 'fuelWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_hshifter_slot.json_path = ('truck', 'shifterSlot')
SCS_TELEMETRY_TRUCK_CHANNEL_lblinker.json_path = ('truck', 'blinkerLeftOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_front.json_path = ('truck', 'lightsAuxFrontOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_front.conv_func = non_zero
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_roof.json_path = ('truck', 'lightsAuxRoofOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_aux_roof.conv_func = non_zero
SCS_TELEMETRY_TRUCK_CHANNEL_light_beacon.json_path = ('truck', 'lightsBeaconOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_brake.json_path = ('truck', 'lightsBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_high_beam.json_path = ('truck', 'lightsBeamHighOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_lblinker.json_path = ('truck', 'blinkerLeftActive')
SCS_TELEMETRY_TRUCK_CHANNEL_light_low_beam.json_path = ('truck', 'lightsBeamLowOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_parking.json_path = ('truck', 'lightsParkingOn')
SCS_TELEMETRY_TRUCK_CHANNEL_light_rblinker.json_path = ('truck', 'blinkerRightActive')
SCS_TELEMETRY_TRUCK_CHANNEL_light_reverse.json_path = ('truck', 'lightsReverseOn')
SCS_TELEMETRY_TRUCK_CHANNEL_local_linear_acceleration.json_path = ('truck', 'acceleration')
SCS_TELEMETRY_TRUCK_CHANNEL_motor_brake.json_path = ('truck', 'motorBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_distance.json_path = ('navigation', 'estimatedDistance')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_distance.conv_func = round
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_speed_limit.json_path = ('navigation', 'speedLimit')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_speed_limit.conv_func = mps_to_kph
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_time.json_path = ('navigation', 'estimatedTime')
SCS_TELEMETRY_TRUCK_CHANNEL_navigation_time.conv_func = lambda v: game_time_ + timedelta(seconds=v)
SCS_TELEMETRY_TRUCK_CHANNEL_odometer.json_path = ('truck', 'odometer')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_pressure.json_path = ('truck', 'oilPressure')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_pressure_warning.json_path = ('truck', 'oilPressureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_oil_temperature.json_path = ('truck', 'oilTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_parking_brake.json_path = ('truck', 'parkBrakeOn')
SCS_TELEMETRY_TRUCK_CHANNEL_rblinker.json_path = ('truck', 'blinkerRightOn')
SCS_TELEMETRY_TRUCK_CHANNEL_retarder_level.json_path = ('truck', 'retarderBrake')
SCS_TELEMETRY_TRUCK_CHANNEL_speed.json_path = ('truck', 'speed')
SCS_TELEMETRY_TRUCK_CHANNEL_speed.conv_func = mps_to_kph
SCS_TELEMETRY_TRUCK_CHANNEL_water_temperature.json_path = ('truck', 'waterTemperature')
SCS_TELEMETRY_TRUCK_CHANNEL_water_temperature_warning.json_path = ('truck', 'waterTemperatureWarningOn')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_cabin.json_path = ('truck', 'wearCabin')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_chassis.json_path = ('truck', 'wearChassis')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_engine.json_path = ('truck', 'wearEngine')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_transmission.json_path = ('truck', 'wearTransmission')
SCS_TELEMETRY_TRUCK_CHANNEL_wear_wheels.json_path = ('truck', 'wearWheels')
SCS_TELEMETRY_TRUCK_CHANNEL_wipers.json_path = ('truck', 'wipersOn')
SCS_TELEMETRY_TRUCK_CHANNEL_world_placement.json_path = ('truck', 'placement')
SCS_TELEMETRY_TRUCK_CHANNEL_world_placement.conv_func = flatten_placement

CONFIG_EVENT_MAP = {
    SCS_TELEMETRY_CONFIG_controls: {
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_shifter_type: ('truck', 'shifterType'),
    },
    SCS_TELEMETRY_CONFIG_job: {
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_mass: ('trailer', 'mass'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_city: ('job', 'destinationCity'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_destination_company: ('job', 'destinationCompany'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_city: ('job', 'sourceCity'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_source_company: ('job', 'sourceCompany'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_income: ('job', 'income'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_delivery_time: ('job', 'deadlineTime', lambda v: GAME_TIME_BASE + timedelta(minutes=v)),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo: ('trailer', 'name'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_id: ('trailer', 'id'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_cargo_mass: ('trailer', 'mass'),
    },
    SCS_TELEMETRY_CONFIG_truck: {
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_adblue_capacity: ('truck', 'adblueCapacity'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_air_pressure_emergency: ('truck', 'airPressureEmergencyValue'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_air_pressure_warning: ('truck', 'airPressureWarningValue'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_battery_voltage_warning: ('truck', 'batteryVoltageWarningValue'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_brand: ('truck', 'make'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_brand_id: ('truck', 'id'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_cabin_position: ('truck', 'cabin'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_forward_gear_count: ('truck', 'forwardGears'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_fuel_capacity: ('truck', 'fuelCapacity'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_fuel_warning_factor: ('truck', 'fuelWarningFactor'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_head_position: ('truck', 'head'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_hook_position: ('truck', 'hook'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_name: ('truck', 'model'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_oil_pressure_warning: ('truck', 'oilPressureWarningValue'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_retarder_step_count: ('truck', 'retarderStepCount'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_reverse_gear_count: ('truck', 'reverseGears'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_rpm_limit: ('truck', 'engineRpmMax'),
        SCS_TELEMETRY_CONFIG_ATTRIBUTE_water_temperature_warning: ('truck', 'waterTemperatureWarningValue'),
    }
}
