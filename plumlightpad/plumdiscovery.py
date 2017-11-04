'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''

from socket import socket, timeout, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST

def discover():
    """Broadcast a query on the network to find all Plum Lightpads"""

    devices = {}
    i = 0
    while i < 2:
        discovery_socket = socket(AF_INET, SOCK_DGRAM)
        discovery_socket.bind(("", 50000))
        discovery_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        discovery_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        discovery_socket.sendto("PLUM".encode("UTF-8"), ("255.255.255.255", 43770))
        discovery_socket.settimeout(5)
        try:
            while True:
                data, source_ip = discovery_socket.recvfrom(1024)
                info = data.decode("UTF-8").split(" ")
                lpid = info[2]

                if lpid not in devices:
                    lightpad = {}
                    lightpad.update({"ip": source_ip[0]})
                    lightpad.update({"port": info[3]})
                    devices.update({lpid: lightpad})
        except timeout:
            pass
        finally:
            discovery_socket.close()
            i += 1

    return devices
