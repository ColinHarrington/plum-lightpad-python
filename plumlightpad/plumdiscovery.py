'''
Plum Lightpad Python Library
https://github.com/heathbar/plum-lightpad-python

Published under the MIT license - See LICENSE file for more details.
'''
import asyncio
import re

class LocalDiscoveryProtocol(asyncio.DatagramProtocol):
    def __init__(self, handler, loop):
        super().__init__()
        self.__handler = handler
        self.__loop = loop
        self.broadcast_count = 0
        self.regex = re.compile("^PLUM (\d+) (?P<lpid>[a-f0-9\-]+) (?P<port>\d+)$")

    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info("socket")
        sock.setblocking(False)
        sock.settimeout(0)
        self.broadcast()

    def broadcast(self):
        if self.broadcast_count < 2:
            self.transport.sendto("PLUM".encode("UTF-8"), ("255.255.255.255", 43770))
            self.broadcast_count += 1
            self.__loop.call_later(15, self.broadcast)

    def datagram_received(self, data, addr):
        matches = self.regex.match(data.decode("UTF-8"))
        if matches is not None:
            lightpad = matches.groupdict()
            lightpad.update({'ip': addr[0]})
            asyncio.ensure_future(self.__handler(lightpad), loop=self.__loop)