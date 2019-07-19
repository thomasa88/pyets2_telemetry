import logging
import threading
#import queue

import telemetry
import web_server

SCS_TELEMETRY_CHANNEL_game_time = "game.time"
SCS_TELEMETRY_TRUCK_CHANNEL_speed = "truck.speed"

SCS_RESULT_ok                        =  0
SCS_RESULT_unsupported               = -1
SCS_RESULT_invalid_parameter         = -2
SCS_RESULT_already_registered        = -3
SCS_RESULT_not_found                 = -4
SCS_RESULT_unsupported_type          = -5
SCS_RESULT_not_now                   = -6
SCS_RESULT_generic_error             = -7

SCS_TELEMETRY_CHANNEL_FLAG_none         = 0x00000000
SCS_TELEMETRY_CHANNEL_FLAG_each_frame   = 0x00000001
SCS_TELEMETRY_CHANNEL_FLAG_no_value     = 0x00000002

# Index
SCS_U32_NIL = -1

SCS_VALUE_TYPE_INVALID           = 0
SCS_VALUE_TYPE_bool              = 1
SCS_VALUE_TYPE_s32               = 2
SCS_VALUE_TYPE_u32               = 3
SCS_VALUE_TYPE_u64               = 4
SCS_VALUE_TYPE_float             = 5
SCS_VALUE_TYPE_double            = 6
SCS_VALUE_TYPE_fvector           = 7
SCS_VALUE_TYPE_dvector           = 8
SCS_VALUE_TYPE_euler             = 9
SCS_VALUE_TYPE_fplacement        = 10
SCS_VALUE_TYPE_dplacement        = 11
SCS_VALUE_TYPE_string            = 12
SCS_VALUE_TYPE_s64               = 13

server_ = None
server_thread_ = None

shared_data_ = {
    'condition': threading.Condition(),
    'telemetry_data': {},
    'new_data': False
}

# Setting up logging, so other threads can log to the game console
class TelemetryLogHandler(logging.Handler):
    # Is locking (thread safety) included in logging.Handler?
    def emit(self, record):
        telemetry.log(self.format(record))

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(TelemetryLogHandler())

def channel_cb(name, index, value, context):
    with shared_data_['condition']:
        shared_data_['new_data'] = True
        if name == SCS_TELEMETRY_TRUCK_CHANNEL_speed:
            shared_data_['telemetry_data']['truck']['speed'] = mps_to_kph(value)
            shared_data_['condition'].notify()

def telemetry_init(version, game_name, game_id, game_version):
    init_shared_data()
    ret = telemetry.register_for_channel(SCS_TELEMETRY_TRUCK_CHANNEL_speed,
                                         SCS_U32_NIL,
                                         SCS_VALUE_TYPE_float,
                                         SCS_TELEMETRY_CHANNEL_FLAG_none,
                                         channel_cb, None)
    if ret != SCS_RESULT_ok:
        raise Exception("Failed to register to channel: %d" % ret)
    start_server()

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

def mps_to_kph(mps):
    return 3.6 * mps

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
            'telemetryPluginVersion': '4'
        },
        'truck': {
            'id': 'man',
            'make': 'MAN',
            'model': 'TGX',
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
            'userSteer': 0.0,
            'userThrottle': 1.0,
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
            'adblueAverageConsumpton': 0.0,
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
            'id': 'derrick',
            'name': 'derrick',
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
            'sourceCity': 'Linz',
            'sourceCompany': 'DPD',
            'destinationCity': 'Salzburg',
            'destinationCompany': 'JCB'
        },
        'navigation': {
            'estimatedTime': '0001-01-01T03: 01: 40Z',
            'estimatedDistance': 0,
            'speedLimit': 90
        }
    }
