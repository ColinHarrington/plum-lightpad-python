'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
import requests

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
        print("device_found:", device)
        lpid = device['lpid']
        if lpid not in self.local_devices:
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
                    await load_listener(logical_load)
            else:
                self.loads[llid].add_lightpad(lightpad)

            for lightpad_listener in self.lightpad_listeners:
                await lightpad_listener(lightpad)
        else:
            print("Already located device", device)

    async def discover(self, loop):
        print("Plum :: discover")

        protocol = LocalDiscoveryProtocol(handler=self.device_found, loop=loop)

        coro = loop.create_datagram_endpoint(
            lambda: protocol, local_addr=('0.0.0.0', 43770), allow_broadcast=True, reuse_port=True)
        asyncio.ensure_future(coro)

        await self._cloud.fetch_all_the_things()  # Cloud Discovery
        # await self._cloud.update()

    def add_load_listener(self, callback):
        self.load_listeners.append(callback)

    def add_lightpad_listener(self, callback):
        self.lightpad_listeners.append(callback)

    def get_logical_loads(self):
        return self.loads

    def get_lightpads(self):
        return self.lightpads

    def cleanup(self):
        for lightpad in self.lightpads.values():
            lightpad.close()
