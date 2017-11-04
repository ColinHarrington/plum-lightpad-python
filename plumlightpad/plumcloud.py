'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''

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
        data = {"lpid":lpid}
        return self.__post(url, data)

    def __post(self, url, data):
        return requests.post(url, headers=self.headers, json=data).json()

def fetch_all_the_things(username, password):
    """Fetch all info from cloud"""
    cloud = PlumCloud(username, password)
    info = {}

    houses = cloud.fetch_houses()
    for house in houses:
        house_details = cloud.fetch_house(house)

        info[house] = {
            "name": house_details["house_name"],
            "timezone": house_details["local_tz"],
            "latlon": house_details["latlong"],
            "location": house_details["location"],
            "token": house_details["house_access_token"],
            "rooms": {}
        }

        for room_id in house_details["rids"]:
            room = cloud.fetch_room(room_id)
            info[house]["rooms"][room_id] = {
                "name": room["room_name"],
                "logical_loads": {}
            }

            for llid in room["llids"]:
                load = cloud.fetch_logical_load(llid)

                info[house]["rooms"][room_id]["logical_loads"][llid] = {
                    "name": load["logical_load_name"],
                    "lightpads": {}
                }

                for lpid in load["lpids"]:
                    lightpad = cloud.fetch_lightpad(lpid)
                    info[house]["rooms"][room_id]["logical_loads"][llid]["lightpads"][lpid] = {
                        "name": lightpad["lightpad_name"],
                        "provisioned": lightpad["is_provisioned"],
                        "custom_gestures": lightpad["custom_gestures"],
                        "config": lightpad["config"]
                    }
    return info
    