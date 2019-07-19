#!/usr/bin/env python3

# SignalR protocol info:
# https://blog.3d-logic.com/2015/03/29/signalr-on-the-wire-an-informal-description-of-the-signalr-protocol/
# http://www.mithril.com.au/SignalR%20Protocol.docx (old protocol version)

import http.server
import json
import socketserver
import time
import urllib

PORT_NUMBER = 25555

config = {
    'skins': [{
        "name": "scania", # Must use directory name - including case!
        "title": "Scania Dashboard",
        "author": "Klauzzy",
        "width": 2030,
        "height": 1035
    }]
}

config_json = json.dumps(config)

negotiate_json = json.dumps(
    {
        "Url":"/signalr",
        "ConnectionToken": "unique_connect_token",
        "ConnectionId": "660fa684-9d01-4c4a-86e7-deb5ad7c6b87",
        "KeepAliveTimeout":6.0,
        "DisconnectTimeout":9.0,
        "ConnectionTimeout":12.0,
        "TryWebSockets": False,
        "ProtocolVersion":"1.5",
        "TransportConnectTimeout":5.0,
        "LongPollDelay": 0.0
    })

connect_json = json.dumps(
    {"C":"s-0,2CDDE7A|1,23ADE88|2,297B01B|3,3997404|4,33239B5","S":1,"M":[]}
)

# Correct?
reconnect_json = json.dumps({})

start_json = json.dumps(
    {"Response":"started"}
)

poll_json = json.dumps(
    {}
)

test_resp = {
   "game":{
      "connected":True,
      "paused":True,
      "time":"0001-01-08T21:09:00Z",
      "timeScale":19.0,
      "nextRestStopTime":"0001-01-01T10:11:00Z",
      "version":"1.10",
      "telemetryPluginVersion":"4"
   },
   "truck":{
      "id":"man",
      "make":"MAN",
      "model":"TGX",
      "speed":53.82604,
      "cruiseControlSpeed":0.0,
      "cruiseControlOn":False,
      "odometer":105830.453,
      "gear":10,
      "displayedGear":10,
      "forwardGears":12,
      "reverseGears":1,
      "shifterType":"arcade",
      "engineRpm":1337.18762,
      "engineRpmMax":2500.0,
      "fuel":683.829834,
      "fuelCapacity":700.0,
      "fuelAverageConsumption":0.4923077,
      "fuelWarningFactor":0.15,
      "fuelWarningOn":False,
      "wearEngine":0.008189549,
      "wearTransmission":0.004930536,
      "wearCabin":0.0130360955,
      "wearChassis":0.0162951164,
      "wearWheels":0.002864266,
      "userSteer":0.0,
      "userThrottle":1.0,
      "userBrake":0.0,
      "userClutch":0.0,
      "gameSteer":0.026530467,
      "gameThrottle":1.0,
      "gameBrake":0.0,
      "gameClutch":0.0,
      "shifterSlot":0,
      "engineOn": False,
      "electricOn":False,
      "wipersOn":False,
      "retarderBrake":0,
      "retarderStepCount":3,
      "parkBrakeOn":False,
      "motorBrakeOn":False,
      "brakeTemperature":15.0831814,
      "adblue":0.0,
      "adblueCapacity":0.0,
      "adblueAverageConsumpton":0.0,
      "adblueWarningOn":False,
      "airPressure":139.999741,
      "airPressureWarningOn":False,
      "airPressureWarningValue":65.0,
      "airPressureEmergencyOn":False,
      "airPressureEmergencyValue":30.0,
      "oilTemperature":57.3665657,
      "oilPressure":70.40637,
      "oilPressureWarningOn":False,
      "oilPressureWarningValue":10.0,
      "waterTemperature":53.1299934,
      "waterTemperatureWarningOn":False,
      "waterTemperatureWarningValue":105.0,
      "batteryVoltage":23.6067848,
      "batteryVoltageWarningOn":False,
      "batteryVoltageWarningValue":22.0,
      "lightsDashboardValue":1.0,
      "lightsDashboardOn":True,
      "blinkerLeftActive":False,
      "blinkerRightActive":False,
      "blinkerLeftOn":False,
      "blinkerRightOn":False,
      "lightsParkingOn":False,
      "lightsBeamLowOn":False,
      "lightsBeamHighOn":False,
      "lightsAuxFrontOn":False,
      "lightsAuxRoofOn":False,
      "lightsBeaconOn":False,
      "lightsBrakeOn":False,
      "lightsReverseOn":False,
      "placement":{
         "x":13475.5762,
         "y":67.3605652,
         "z":14618.6211,
         "heading":0.185142234,
         "pitch":-0.0067760786,
         "roll":-0.000293774
      },
      "acceleration":{
         "x":0.0214568116,
         "y":0.00623101648,
         "z":-0.759649038
      },
      "head":{
         "x":-0.795116067,
         "y":1.43522251,
         "z":-0.08483863
      },
      "cabin":{
         "x":0.0,
         "y":1.36506855,
         "z":-1.70362806
      },
      "hook":{
         "x":0.0,
         "y":0.939669,
         "z":-6.17736959
      }
   },
   "trailer":{
      "attached":True,
      "id":"derrick",
      "name":"Вышка",
      "mass":22000.0,
      "wear":0.0234265551,
      "placement":{
         "x":13483.3223,
         "y":67.73905,
         "z":14622.127,
         "heading":0.1813016,
         "pitch":-0.00583146373,
         "roll":-0.000160016149
      }
   },
   "job":{
      "income":2316,
      "deadlineTime":"0001-01-09T03:34:00Z",
      "remainingTime":"0001-01-01T06:25:00Z",
      "sourceCity":"Linz",
      "sourceCompany":"DPD",
      "destinationCity":"Salzburg",
      "destinationCompany":"JCB"
   },
   "navigation":{
      "estimatedTime": "0001-01-01T03:01:40Z",
      "estimatedDistance": 132500,
      "speedLimit": 90
   }
}

class SignalrHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, request, client_address, server):
        super().__init__(request, client_address, server)
        self.protocol_version = 'HTTP/1.1'

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if not self.do_signalr():
            super().do_GET()

    def do_POST(self):
        if not self.do_signalr():
            super().do_POST()

    def do_signalr(self):
        try:
            return self.do_signalr_comm()
        except BrokenPipeError:
            # Client closed connection. Most likely left the web page.
            return True

    def do_signalr_comm(self):
        processed = True
        if self.path.startswith('/config.json'):
            self.read_data()
            self.write_response(config_json)
        elif self.path.startswith('/signalr/hubs'):
            # This response is too complex. Handing over to the file server.
            processed = False
        elif self.path.startswith('/signalr/negotiate'):
            self.read_data()
            self.write_response(negotiate_json)
        elif self.path.startswith('/signalr/start'):
            self.read_data()
            self.write_response(start_json)
        elif self.path.startswith('/signalr/connect'):
            self.read_data()
            self.write_response(connect_json)
        elif self.path.startswith('/signalr/reconnect'):
            self.read_data()
            self.write_response(reconnect_json)
        elif self.path.startswith('/signalr/poll'):
            data = self.read_data()
            post_data = urllib.parse.parse_qs(data)
            messageId = post_data['messageId'][0]
            
            # Should not respond until new data is available?
            time.sleep(1)
            
            poll_data_json = json.dumps(
                {
                    'C': messageId,
                    'M': [
                        { 'H': 'ets2telemetryhub',
                          'M': 'UpdateData',
                          'A': [json.dumps(test_resp)] }
                    ]
                }
                )
            # When there is no new data, send "{}" to avoid timeout
            self.write_response(poll_data_json)
        elif self.path.startswith('/signalr/send'):
            data = self.read_data()
            post_data = urllib.parse.parse_qs(data)
            json_req = post_data['data'][0]
            req = json.loads(json_req)
            method = req['M']
            args = req['A']
            id = req['I']

            # TODO: if method == RequestData

            resp = { 'I': id,
                     'R': test_resp }
            resp_json = json.dumps(resp)
            
            self.write_response(resp_json)
        else:
            processed = False
        return processed

        
    def read_data(self):
        length = self.headers['Content-Length']
        if length is None:
            return bytes()
        else:
            utf8_data = self.rfile.read(int(length))
            return utf8_data.decode('utf-8')

    def write_response(self, data):
        utf8_data = data.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=UTF-8')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Content-Length', len(utf8_data))
        # TODO: Transfer-Encoding: chunked. Will likely affect shutdown behavior.
        self.end_headers()
        self.wfile.write(utf8_data)


# Python 3.7 has built-in ThreadingHTTPServer, but Python 3.6 does not
class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

server = ThreadingHTTPServer(('', PORT_NUMBER), SignalrHandler)
print('Started server on port', PORT_NUMBER)

server.serve_forever()
