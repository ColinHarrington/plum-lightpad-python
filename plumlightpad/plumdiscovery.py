'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
from threading import Thread
from socket import socket, timeout, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
#
# class LocalDiscovery(Thread):
#     def __init__(self, callback, loop):
#         super().__init__()
#         self.__device_handler = callback
#         self.__loop = loop

async def local_discovery(device_handler):
    """Broadcast a query on the network to find all Plum Lightpads"""

    devices = {}
    i = 0
    while i < 2:
        i += 1
        discovery_socket = socket(AF_INET, SOCK_DGRAM)
        discovery_socket.bind(("", 0))
        discovery_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        discovery_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        discovery_socket.setblocking(False)
        discovery_socket.sendto("PLUM".encode("UTF-8"), ("255.255.255.255", 43770))
        discovery_socket.settimeout(5)
        try:
            while True:
                data, source_ip = discovery_socket.recvfrom(1024)
                info = data.decode("UTF-8").split(" ")
                lpid = info[2]

                if lpid not in devices:
                    lightpad = {
                        "lpid": info[2],
                        "ip": source_ip[0],
                        "port": info[3]
                    }
                    asyncio.ensure_future(device_handler(lightpad))
                    devices[lpid] = lightpad

        except timeout:
            pass
        finally:
            print("Done with local discovery....")
            discovery_socket.close()