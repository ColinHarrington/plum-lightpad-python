'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''

import time
import hashlib
import requests

import plumdiscovery
import plumcloud

class PlumLightpad:
    """Interact with Plum Lightpad devices"""

    def __init__(self, username, password):
        print("")
        self.local_devices = plumdiscovery.discover()
        cloud_data = plumcloud.fetch_all_the_things(username, password)
        self.loads = self.__collate_logical_loads(cloud_data, self.local_devices)

    def turn_on(self, llid):
        """Turn on a logical load"""
        self.set_level(llid, 255)

    def turn_off(self, llid):
        """Turn off a logical load"""
        self.set_level(llid, 0)

    def set_level(self, llid, level):
        """Turn on a logical load"""

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

                    if response.status_code is 200:
                        return

                except IOError:
                    print('error')

    def __post(self, url, data, token):
        headers = {
            "User-Agent": "Plum/2.3.0 (iPhone; iOS 9.2.1; Scale/2.00)",
            "X-Plum-House-Access-Token": token
        }
        return requests.post(url, headers=headers, json=data, verify=False)

    def __collate_logical_loads(self, cloud_data, devices):
        """Make a list of all logical loads from the cloud with only the lightpads found on the current network"""

        collated_loads = {}
        sha = hashlib.new("sha256")

        for house_id in cloud_data:
            rooms = cloud_data[house_id]["rooms"]

            for room_id in rooms:
                logical_loads = cloud_data[house_id]["rooms"][room_id]["logical_loads"]

                for load_id in logical_loads:
                    load = cloud_data[house_id]["rooms"][room_id]["logical_loads"][load_id]

                    sha.update(cloud_data[house_id]["token"].encode())
                    token = sha.hexdigest()

                    collated_loads[load_id] = {
                        "name": load["name"],
                        "token": token,
                        "lightpads": {}
                    }

                    for lpid in load["lightpads"]:
                        if lpid in devices:
                            collated_loads[load_id]["lightpads"][lpid] = load["lightpads"][lpid]
                            collated_loads[load_id]["lightpads"][lpid]["ip"] = devices[lpid]["ip"]
                            collated_loads[load_id]["lightpads"][lpid]["port"] = devices[lpid]["port"]

        return collated_loads
