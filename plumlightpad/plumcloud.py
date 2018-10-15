'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''

import asyncio
import hashlib
import sys
import base64


class PlumCloud():
    """Interact with Plum Cloud"""

    def __init__(self, username, password):
        auth = base64.b64encode(("%s:%s" % (username, password)).encode())
        self.headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "Authorization": "Basic %s" % (auth.decode()),
        }
        self.houses = {}
        self.rooms = {}
        self.logical_loads = {}
        self.lightpads = {}

    async def get_load_data(self, llid):
        while llid not in self.logical_loads:
            await asyncio.sleep(0.1)  # TODO change this to a wait with a timeout?
        return self.logical_loads[llid]

    async def get_lightpad_data(self, lpid):
        while lpid not in self.lightpads:
            await asyncio.sleep(0.1)  # TODO change this to a wait with a timeout?
        return self.lightpads[lpid]

    async def fetch_houses(self):
        """Lookup details for devices on the plum servers"""
        try:
            async with self._websession.get("https://production.plum.technology/v2/getHouses", headers=self.headers) as response:
                return await response.json()

        except IOError:
            print("Unable to login to Plum cloud servers.")
            sys.exit(5)

    async def fetch_house(self, house_id):
        """Lookup details for a given house id"""
        url = "https://production.plum.technology/v2/getHouse"
        data = {"hid": house_id}
        return await self.__post(url, data)

    async def fetch_room(self, room_id):
        """Lookup details for a given room id"""
        url = "https://production.plum.technology/v2/getRoom"
        data = {"rid": room_id}
        return await self.__post(url, data)

    async def fetch_logical_load(self, llid):
        """Lookup details for a given logical load"""
        url = "https://production.plum.technology/v2/getLogicalLoad"
        data = {"llid": llid}
        return await self.__post(url, data)

    async def fetch_lightpad(self, lpid):
        """Lookup details for a given lightpad"""
        url = "https://production.plum.technology/v2/getLightpad"
        data = {"lpid": lpid}
        return await self.__post(url, data)

    async def __post(self, url, data):
        response = await self._websession.post(url, headers=self.headers, json=data)
        return await response.json()

    async def update_houses(self):
        """Lookup details for devices on the plum servers"""
        houses = await self.fetch_houses()
        for house_id in houses:
            asyncio.Task(self.update_house(house_id))

    async def update_house(self, house_id):
        house = await self.fetch_house(house_id)
        self.houses[house_id] = house

        sha = hashlib.new("sha256")
        sha.update(house["house_access_token"].encode())
        house['access_token'] = sha.hexdigest()

        for room_id in house['rids']:
            asyncio.Task(self.update_room(room_id=room_id, house=house))

    async def update_room(self, room_id, house):
        room = await self.fetch_room(room_id)
        room['house'] = house
        self.rooms[room_id] = room
        for llid in room["llids"]:
            asyncio.Task(self.update_logical_load(llid=llid, house=house, room=room))

    async def update_logical_load(self, llid, house, room):
        logical_load = await self.fetch_logical_load(llid)
        logical_load['room'] = room
        self.logical_loads[llid] = logical_load
        await asyncio.gather(
            *[self.update_lightpad(lpid=lpid, house=house, room=room, logical_load=logical_load) for lpid in
              logical_load['lpids']])

    async def update_lightpad(self, lpid, house, room, logical_load):
        lightpad = await self.fetch_lightpad(lpid)
        lightpad['house'] = house
        lightpad['room'] = room
        lightpad['logical_load'] = logical_load
        lightpad['access_token'] = house['access_token']
        self.lightpads[lpid] = lightpad

    async def update(self, websession):
        self._websession = websession
        """Fetch all info from cloud"""
        await self.update_houses()
