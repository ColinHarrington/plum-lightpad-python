import asyncio

class LightpadHeartbeatProtocol(asyncio.DatagramProtocol):
    def __init__(self, handler):
        super().__init__()
        self._handler = handler

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(addr, data)
        self._handler(addr, data)