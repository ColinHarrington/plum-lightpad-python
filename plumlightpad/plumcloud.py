'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
import hashlib
import sys
import base64
import requests


class PlumCloud():
    """Interact with Plum Cloud"""

    def __init__(self, username, password):
        auth = base64.b64encode(("%s:%s" % (username, password)).encode())
        self.headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "Authorization": "Basic %s" % (auth.decode()),
        }
        self.logical_loads = {}
        self.lightpads = {}

    @property
    def data(self):
        return self._cloud_info

    async def get_load_data(self, llid):
        while self.logical_loads[llid] is None:
            await asyncio.sleep(0.1) #TODO change this to a wait with a timeout?
        return self.logical_loads[llid]

    async def get_lightpad_data(self, lpid):
        while self.lightpads[lpid] is None:
            await asyncio.sleep(0.1) #TODO change this to a wait with a timeout?
        return self.lightpads[lpid]


    def fetch_houses(self):
        """Lookup details for devices on the plum servers"""
        try:
            url = "https://production.plum.technology/v2/getHouses"
            return requests.get(url, headers=self.headers).json()
        except IOError:
            print("Unable to login to Plum cloud servers.")
            sys.exit(5)

    def fetch_house(self, house_id):
        """Lookup details for a given house id"""
        url = "https://production.plum.technology/v2/getHouse"
        data = {"hid": house_id}
        return self.__post(url, data)

    def fetch_room(self, room_id):
        """Lookup details for a given room id"""
        url = "https://production.plum.technology/v2/getRoom"
        data = {"rid": room_id}
        return self.__post(url, data)

    def fetch_logical_load(self, llid):
        """Lookup details for a given logical load"""
        url = "https://production.plum.technology/v2/getLogicalLoad"
        data = {"llid": llid}
        return self.__post(url, data)

    def fetch_lightpad(self, lpid):
        """Lookup details for a given lightpad"""
        url = "https://production.plum.technology/v2/getLightpad"
        data = {"lpid": lpid}
        return self.__post(url, data)

    def __post(self, url, data):
        return requests.post(url, headers=self.headers, json=data).json()


    def fetch_all_the_things(self):  # TODO make this async
        """Fetch all info from cloud"""
        cloud_info = {}

        houses = self.fetch_houses()

        sha = hashlib.new("sha256")

        for house in houses:
            house_details = self.fetch_house(house)
            print(house, house_details)
            cloud_info[house] = house_details


            sha.update(house_details["house_access_token"].encode())
            access_token = sha.hexdigest()

            house_details['rooms'] = {}
            for room_id in house_details["rids"]:
                room = self.fetch_room(room_id)
                print("Room:", room)
                cloud_info[house]["rooms"][room_id] = room

                room['logical_loads'] = {}
                for llid in room["llids"]:
                    logical_load = self.fetch_logical_load(llid)
                    self.logical_loads[llid] = logical_load
                    self.logical_loads[llid]['room'] = room
                    print("LogicalLoad:", logical_load)
                    cloud_info[house]["rooms"][room_id]["logical_loads"][llid] = logical_load

                    logical_load['lightpads'] = {}
                    for lpid in logical_load["lpids"]:
                        lightpad = self.fetch_lightpad(lpid)
                        print("Lightpad:", lightpad)
                        cloud_info[house]["rooms"][room_id]["logical_loads"][llid]["lightpads"][lpid] = lightpad
                        self.lightpads[lpid] = lightpad

                        self.lightpads[lpid]['access_token'] = access_token
                        self.lightpads[lpid]['house'] = house_details

        self._cloud_info = cloud_info
        return cloud_info
