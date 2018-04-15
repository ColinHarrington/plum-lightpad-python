'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
from datetime import datetime

import aiohttp
import asyncio
import hashlib
import json
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

    @property
    def data(self):
        return self._cloud_info

    async def get_load_data(self, llid):
        while llid not in self.logical_loads:
            await asyncio.sleep(0.1) #TODO change this to a wait with a timeout?
        return self.logical_loads[llid]

    async def get_lightpad_data(self, lpid):
        while lpid not in self.lightpads:
            await asyncio.sleep(0.1) #TODO change this to a wait with a timeout?
        return self.lightpads[lpid]

    async def fetch_houses(self):
        """Lookup details for devices on the plum servers"""
        try:
            url = "https://production.plum.technology/v2/getHouses"
            async with aiohttp.ClientSession() as session:
                response = await session.request('GET', url, headers=self.headers)
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
        async with aiohttp.ClientSession() as session:
            response = await session.request('POST', url, data=json.dumps(data), headers=self.headers)
            return await response.json()

    async def update_houses(self):
        """Lookup details for devices on the plum servers"""
        houses = await self.fetch_houses()
        for house_id in houses:
            asyncio.Task(self.update_house(house_id))

    async def update_house(self, house_id):
        house = await self.fetch_house(house_id)

        self.houses[house_id] = house

    async def sync(self):  # TODO make this async
        """Fetch all info from cloud"""
        async with aiohttp.ClientSession() as session:
            self.__session = session
            cloud_info = {}

            print("starting Cloud Sync", datetime.utcnow())
            tasks = []
            houses = await self.fetch_houses()


            # sha = hashlib.new("sha256")

            for house in houses:
                async def f_house(house):
                    house_details = await self.fetch_house(house)
                    print(house, house_details)
                    cloud_info[house] = house_details
                    async def f_room(room_id):
                        room = await self.fetch_room(room_id)
                        print(room)
                        async def f_load(llid):
                            logical_load = await self.fetch_logical_load(llid)
                            print(logical_load)
                            async def f_lightpad(lpid):
                                lightpad = await self.fetch_lightpad(lpid)
                                print(lightpad)
                            for lpid in logical_load["lpids"]:
                                tasks.append(asyncio.Task(f_lightpad(lpid)))
                        for llid in room["llids"]:
                            tasks.append(asyncio.Task(f_load(llid)))
                    for room_id in house_details["rids"]:
                        tasks.append(asyncio.Task(f_room(room_id)))
                tasks.append(asyncio.Task(f_house(house)))
            asyncio.gather(*tasks)
            print("Finished Cloud Sync", datetime.utcnow())
            self._cloud_info = cloud_info
            return cloud_info


    async def fetch_all_the_things(self):  # TODO make this async
        """Fetch all info from cloud"""
        async with aiohttp.ClientSession() as session:
            self.__session = session
            cloud_info = {}

            houses = self.fetch_houses()

            sha = hashlib.new("sha256")

            for house in await houses:
                house_details = await self.fetch_house(house)
                print(house, house_details)
                cloud_info[house] = house_details


                sha.update(house_details["house_access_token"].encode())
                access_token = sha.hexdigest()

                house_details['rooms'] = {}
                for room_id in house_details["rids"]:
                    room = await self.fetch_room(room_id)
                    print("Room:", room)
                    cloud_info[house]["rooms"][room_id] = room

                    room['logical_loads'] = {}
                    for llid in room["llids"]:
                        logical_load = await self.fetch_logical_load(llid)
                        self.logical_loads[llid] = logical_load
                        self.logical_loads[llid]['room'] = room
                        print("LogicalLoad:", logical_load)
                        cloud_info[house]["rooms"][room_id]["logical_loads"][llid] = logical_load

                        logical_load['lightpads'] = {}
                        for lpid in logical_load["lpids"]:
                            lightpad = await self.fetch_lightpad(lpid)
                            print("Lightpad:", lightpad)
                            cloud_info[house]["rooms"][room_id]["logical_loads"][llid]["lightpads"][lpid] = lightpad
                            self.lightpads[lpid] = lightpad

                            self.lightpads[lpid]['access_token'] = access_token
                            self.lightpads[lpid]['house'] = house_details

            self._cloud_info = cloud_info
            return cloud_info
