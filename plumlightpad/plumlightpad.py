'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
import hashlib
import socket
import threading
import telnetlib
import json
import requests

# from plumlightpad.heartbeat import LightpadHeartbeatProtocol
from plumlightpad.heartbeat import LightpadHeartbeatProtocol
from plumlightpad.logicalload import LogicalLoad
from plumlightpad.plumcloud import PlumCloud
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from plumlightpad.lightpad import Lightpad
from plumlightpad.plumdiscovery import LocalDiscoveryProtocol

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from . import plumdiscovery
from . import plumcloud


class Plum:
    """Interact with Plum Lightpad devices"""

    def __init__(self, username, password):
        self._cloud = PlumCloud(username, password)
        self.local_devices = {}
        self.loads = {}
        self.lightpads = {}
        self.load_listeners = []
        self.lightpad_listeners = []

    async def device_found(self, device):
        lpid = device['lpid']
        self.local_devices[lpid] = device
        data = await self._cloud.get_lightpad_data(lpid)
        lightpad = Lightpad(device=device, data=data)

        self.lightpads[lpid] = lightpad

        llid = lightpad.llid
        if llid not in self.loads:
            load_data = await self._cloud.get_load_data(llid)
            logical_load = LogicalLoad(data=load_data)
            self.loads[llid] = logical_load
            logical_load.add_lightpad(lightpad)
            await logical_load.load_metrics()
            for load_listener in self.load_listeners:
                load_listener(logical_load)  ## TODO event dispatch not on this thread?
        else:
            self.loads[llid].add_lightpad(lightpad)

        for lightpad_listener in self.lightpad_listeners:
            lightpad_listener(lightpad)

    def handle_heartbeat(self, src_addr, data):
        print("HEARTBEAT:", src_addr, data)
        info = data.decode("UTF-8").split(" ")
        if len(info) >= 4:
            lpid = info[2]

            if lpid not in self.local_devices:
                lightpad = {
                    "lpid": info[2],
                    "ip": src_addr[0],
                    "port": info[3]
                }
                self.local_devices[lpid] = lightpad
                asyncio.ensure_future(self.device_found(lightpad))


    async def discover(self):
        loop = asyncio._get_running_loop()
        # asyncio.ensure_future(plumdiscovery.local_discovery(device_handler=self.device_found))

        # protocol = LocalDiscoveryProtocol(device_handler=self.device_found)
        # coro1 = loop.create_datagram_endpoint(
        #     lambda: protocol, local_addr=('0.0.0.0', 50000), reuse_address=True, allow_broadcast=True, family=socket.AF_INET)
        # asyncio.ensure_future(coro1)

        plumdiscovery.LocalDiscovery(loop=loop, device_handler=self.device_found).start()

        protocol = LightpadHeartbeatProtocol(handler=self.handle_heartbeat)
        coro = loop.create_datagram_endpoint(
            lambda: protocol, local_addr=('0.0.0.0', 43770))
        asyncio.ensure_future(coro)
        # coroutine AbstractEventLoop.create_datagram_endpoint(
        #       protocol_factory, local_addr=None, remote_addr=None, *, family=0,
        #                                            proto=0, flags=0, reuse_address=None, reuse_port=None,
        #                                            allow_broadcast=None, sock=None)
        await self._cloud.fetch_all_the_things()  # Cloud Discovery
        # await self._cloud.sync()

    def add_load_listener(self, callback):
        self.load_listeners.append(callback)

    def add_lightpad_listener(self, callback):
        self.lightpad_listeners.append(callback)

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

    def set_lightpad_config(self, lpid, config):
        if lpid in self.lightpads:
            try:
                lightpad = self.lightpads[lpid]
                llid = lightpad["logical_load_id"]

                url = "https://%s:%s/v2/setLogicalLoadConfig" % (lightpad["ip"], lightpad["port"])
                data = {
                    "config": config,
                    "llid": llid
                }
                response = self.__post(url, data, self.loads[llid]["token"])
                print(response)

            except IOError:
                print('error')

    def __post(self, url, data, access_token):
        headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "X-Plum-House-Access-Token": access_token
        }
        return requests.post(url, headers=headers, json=data, verify=False)

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
