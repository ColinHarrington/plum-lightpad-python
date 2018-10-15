'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
import logging

from plumlightpad.logicalload import LogicalLoad
from plumlightpad.plumcloud import PlumCloud
from plumlightpad.lightpad import Lightpad
from plumlightpad.plumdiscovery import LocalDiscoveryProtocol

_LOGGER = logging.getLogger('plumlightpad')


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
        _LOGGER.debug("device_found: %s", device)
        lpid = device['lpid']
        if lpid not in self.local_devices:
            self.local_devices[lpid] = device
            data = await self._cloud.get_lightpad_data(lpid)
            lightpad = Lightpad(device=device, data=data, websession=self._websession)

            self.lightpads[lpid] = lightpad

            llid = lightpad.llid
            if llid not in self.loads:
                load_data = await self._cloud.get_load_data(llid)
                logical_load = LogicalLoad(data=load_data)
                self.loads[llid] = logical_load
                logical_load.add_lightpad(lightpad)
                await logical_load.load_metrics()
                for load_listener in self.load_listeners:
                    await load_listener({'llid': llid})
            else:
                self.loads[llid].add_lightpad(lightpad)

            for lightpad_listener in self.lightpad_listeners:
                await lightpad_listener({'lpid': lpid})
        else:
            _LOGGER.debug("Already located device", device)

    async def loadCloudData(self, websession):
        await self._cloud.update(websession)

    async def discover(self, loop, loadListener=None, lightpadListener=None, websession=None):
        _LOGGER.debug("Plum :: discover")
        if loadListener:
            self.load_listeners.append(loadListener)
        if lightpadListener:
            self.lightpad_listeners.append(lightpadListener)
        self._websession = websession

        protocol = LocalDiscoveryProtocol(handler=self.device_found, loop=loop)

        coro = loop.create_datagram_endpoint(
            lambda: protocol, local_addr=('0.0.0.0', 43770), allow_broadcast=True, reuse_port=True)
        asyncio.ensure_future(coro)

    def add_load_listener(self, callback):
        self.load_listeners.append(callback)

    def add_lightpad_listener(self, callback):
        self.lightpad_listeners.append(callback)

    def get_logical_loads(self):
        return self.loads

    def get_load(self, llid):
        return self.loads[llid]

    def get_lightpads(self):
        return self.lightpads

    def get_lightpad(self, lpid):
        return self.lightpads[lpid]

    def cleanup(self):
        for lightpad in self.lightpads.values():
            lightpad.close()
