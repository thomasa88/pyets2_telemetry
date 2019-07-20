import logging
import threading

import telemetry
import web_server
from scs_defs import *

server_ = None
server_thread_ = None

# NOTE: new_data indicator only works well with 1 client.
# Need to track connection/session ids to handle multiple clients.
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

def telemetry_init(version, game_name, game_id, game_version):
    init_shared_data()
    for i, channel in enumerate(SCS_CHANNELS):
        if not channel.json_name:
            continue
        if channel.indexed:
            index = 0
        else:
            index = None
        register_for_channel(channel, i, index)
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
    channel = SCS_CHANNELS[context]
    with shared_data_['condition']:
        shared_data_['new_data'] = True
        if not isinstance(channel.json_name[0], list):
            if name == SCS_TELEMETRY_TRUCK_CHANNEL_speed:
                logging.info("CB: %f %s %s", value, repr(channel), channel.json_name[0], channel.json_name[1])
            shared_data_['telemetry_data'][channel.json_name[0]][channel.json_name[1]] = channel.conversion_func(value)
        else:
            for i in range(0, len(channel.json_name)):
                shared_data_['telemetry_data'][channel.json_name[i][0]][channel.json_name[i][1]] = channel.conversion_func[i](value)
        shared_data_['condition'].notify()
   
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
            'telemetryPluginVersion': '4'
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
            'remainingTime': '0001-01-01T06: 25: 00Z', # delivery_time - game_time
            'sourceCity': '<sourceCity>',
            'sourceCompany': '<sourceCompany>',
            'destinationCity': '<destinationCity>',
            'destinationCompany': '<destinationCompany>'
        },
        'navigation': {
            'estimatedTime': '0001-01-01T03: 01: 40Z', # navigation_time + game_time?
            'estimatedDistance': 0,
            'speedLimit': 90
        }
    }
