from async_services.base import BaseService


class TCPService(BaseService):
    host = None
    port = None

    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def read(self):
        pass

    async def send(self, send):
        pass

class ZMQService(BaseService):
    def __init__(self, host, port):
        self.host = host
        self.port = port

    async def read(self):
        pass

class GRPCService(BaseService):
    pass

class MulticastService(BaseService):
    pass
