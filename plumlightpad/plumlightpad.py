'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''

import time
import hashlib
import threading
import telnetlib
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from . import plumdiscovery
from . import plumcloud

class Plum:
    """Interact with Plum Lightpad devices"""

    def __init__(self, username, password):
        self.local_devices = plumdiscovery.discover()
        cloud_data = plumcloud.fetch_all_the_things(username, password)
        self.__collate_discoveries(cloud_data, self.local_devices)
        self._subscribers = {}

    def get_logical_loads(self):
        return self.loads

    def get_lightpads(self):
        return self.lightpads

    def get_lightpad_metrics(self, lpid):
        """Get the current metrics of the given lightpad"""
        if lpid in self.lightpads:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]
                url = url = "https://%s:%s/v2/getLogicalLoadMetrics" % (lightpad["ip"], lightpad["port"])
                data = {
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

                if response.status_code is 200:
                    for lp in response.json()["lightpad_metrics"]:
                        if lp["lpid"] == lpid:
                            return lp
                    print("Uh oh, response didn't contain the lpid we asked for!")
                    return

            except IOError:
                print('error')

    def get_logical_load_metrics(self, llid):
        """Get the current metrics of the given logical load"""
        if llid in self.loads:
            # loop through lightpads until one works
            for lpid in self.loads[llid]["lightpads"]:
                try:
                    lightpad = self.loads[llid]["lightpads"][lpid]
                    url = url = "https://%s:%s/v2/getLogicalLoadMetrics" % (lightpad["ip"], lightpad["port"])
                    data = {
                        "llid": llid
                    }
                    response = self.__post(url, data, self.loads[llid]["token"])

                    if response.status_code is 200:
                        return response.json()

                except IOError:
                    print('error')

    def set_lightpad_level(self, lpid, level):
        """Turn on a logical load to a specific level"""

        if lpid in self.lightpads:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]
                url = "https://%s:%s/v2/setLogicalLoadLevel" % (lightpad["ip"], lightpad["port"])
                data = {
                    "level": level,
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

            except IOError:
                print('error')

    def set_logical_load_level(self, llid, level):
        """Turn on a logical load to a specific level"""

        if llid in self.loads:
            # loop through lightpads until one works
            for lpid in self.loads[llid]["lightpads"]:
                try:
                    lightpad = self.loads[llid]["lightpads"][lpid]
                    url = "https://%s:%s/v2/setLogicalLoadLevel" % (lightpad["ip"], lightpad["port"])
                    data = {
                        "level": level,
                        "llid": llid
                    }
                    response = self.__post(url, data, self.loads[llid]["token"])

                except IOError:
                    print('error')

    def turn_lightpad_on(self, lpid):
        """Turn on a lightpad"""
        self.set_lightpad_level(lpid, 255)

    def turn_logical_load_on(self, llid):
        """Turn on a logical load"""
        self.set_logical_load_level(llid, 255)

    def turn_lightpad_off(self, lpid):
        """Turn off a lightpad"""
        self.set_lightpad_level(lpid, 0)

    def turn_logical_load_off(self, llid):
        """Turn off a logical load"""
        self.set_logical_load_level(llid, 0)

    def set_glow_color(self, lpid, r, g, b, w):
        if lpid in self.lightpads:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]

                url = "https://%s:%s/v2/setLogicalLoadConfig" % (lightpad["ip"], lightpad["port"])
                data = {
                    "config": {
                        "glowColor": {
                            "red": r,
                            "green": g,
                            "blue": b,
                            "white": w
                        }
                    },
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

            except IOError:
                print('error')
    
    def set_glow_timeout(self, lpid, timeout):
        if lpid in self.lightpads and timeout >= 0:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]

                url = "https://%s:%s/v2/setLogicalLoadConfig" % (lightpad["ip"], lightpad["port"])
                data = {
                    "config": {
                        "glowTimeout": timeout
                    },
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

            except IOError:
                print('error')

    def set_glow_intensity(self, lpid, intensity):
        if lpid in self.lightpads and intensity >= 0:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]

                url = "https://%s:%s/v2/setLogicalLoadConfig" % (lightpad["ip"], lightpad["port"])
                data = {
                    "config": {
                        "glowIntensity": (float(intensity)/float(100))
                    },
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

            except IOError:
                print('error')

    def enable_glow(self, lpid):
        self.__enable_glow(lpid, True)
    
    def disable_glow(self, lpid):
        self.__enable_glow(lpid, False)

    def register_event_listener(self, lpid, callback):
        """Listens for events from the lightpad"""

        if lpid in self.lightpads:
            lightpad = self.lightpads[lpid]
            self._subscribers[lpid] = threading.Thread(target=self.__register_listener, args=(lightpad["ip"], callback))
            self._subscribers[lpid].daemon = True
            self._subscribers[lpid].start()

    def __register_listener(self, ip, callback):
        """creates a telnet connection to the lightpad"""

        tn = telnetlib.Telnet(ip, 2708)
        self._last_event = ""
        while True:
            try:
                raw_string = tn.read_until(b'.\n', 60)

                if len(raw_string) >= 2 and raw_string[-2:] == b'.\n':
                    # lightpad sends ".\n" at the end that we need to chop off
                    json_string = raw_string.decode('ascii')[0:-2]
                    if json_string != self._last_event:
                        callback(json.loads(json_string))

                    self._last_event = json_string

            except:
                pass

    def __post(self, url, data, token):
        headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "X-Plum-House-Access-Token": token
        }
        return requests.post(url, headers=headers, json=data, verify=False)

    def __collate_discoveries(self, cloud_data, devices):
        """Make a list of all logical loads from the cloud with only the lightpads found on the current network"""

        self.loads = {}
        sha = hashlib.new("sha256")

        for house_id in cloud_data:
            rooms = cloud_data[house_id]["rooms"]

            for room_id in rooms:
                logical_loads = cloud_data[house_id]["rooms"][room_id]["logical_loads"]

                for load_id in logical_loads:
                    load = cloud_data[house_id]["rooms"][room_id]["logical_loads"][load_id]

                    sha.update(cloud_data[house_id]["token"].encode())
                    token = sha.hexdigest()

                    self.loads[load_id] = {
                        "name": load["name"],
                        "token": token,
                        "lightpads": {}
                    }

                    self.lightpads = {}
                    for lpid in load["lightpads"]:
                        if lpid in devices:
                            # reference it by logical load
                            self.loads[load_id]["lightpads"][lpid] = load["lightpads"][lpid]
                            self.loads[load_id]["lightpads"][lpid]["ip"] = devices[lpid]["ip"]
                            self.loads[load_id]["lightpads"][lpid]["port"] = devices[lpid]["port"]

                            # reference it by lightpad
                            self.lightpads[lpid] = load["lightpads"][lpid]
                            self.lightpads[lpid]["ip"] = devices[lpid]["ip"]
                            self.lightpads[lpid]["port"] = devices[lpid]["port"]
                            self.lightpads[lpid]["logical_load_id"] = load_id

    def __enable_glow(self, lpid, enable):
        if lpid in self.lightpads:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]

                url = "https://%s:%s/v2/setLogicalLoadConfig" % (lightpad["ip"], lightpad["port"])
                data = {
                    "config": {
                        "glowEnabled": enable
                    },
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])

                if response.status_code is 200:
                    return

            except IOError:
                print('error')

