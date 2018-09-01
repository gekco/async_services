import asyncio

from asgiref.sync import sync_to_async

from base.clients import BaseClient
from common.utils import log_exception

class ServiceContext:
    client = None
    handler_class = None
    handler = None
    name = ""

    def __init__(self, client, handler_class, name, handler_kwargs=None):
        self.client = client
        self.handler_class = handler_class
        if not handler_kwargs:
            handler_kwargs = {}
        self.handler = self.handler_class(**handler_kwargs)
        self.name = name
        self.handler.context = {"client": client, "name" :name}

    def on_message(self, message):
        self.handler.handle(message)

class ServiceManager:
    """
    class to manage connection of webserver for various 3rd party services
    (Trading Engine MarketData Server Etc)
    """
    active_services = {}
    active_coros = {}
    master_queue = asyncio.Queue()
    queue_listen_coro = None

    def __init__(self, receive_timeout=0.1):
        # initialize event loop
        try:
            self.event_loop = asyncio.get_event_loop()
        except Exception as e:
            log_exception(e)
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)

        # initialize listening to the MAJOR queue
        asyncio.ensure_future(self.receive_queue_coro())
        self.receive_timeout= receive_timeout

    def initialise_services(self, services):
        """
        initialize trading/mktdata services from settings
        :return: None
        """

        for service_name, service_info in services.items():
            self.add_service(service_name, service_info["client"], service_info["handler"] )

    def add_service(self, name, client, service_handler):
        """
        add client
        :return:
        """
        # -- checks
        assert name in self.active_services.keys(), "Service Already Exists With Name {0}".format(name)
        assert issubclass(type(client), BaseClient), "Service {0} not a subclass of BaseService".format(name)

        service_context =  ServiceContext(client, service_handler)
        self.active_services[name] = service_context
        #if to initialize before receive

        if asyncio.iscoroutinefunction(client.receive):
            coro = client.recieve()
            is_blocking = False
        else:
            coro = sync_to_async(client.recieve)
            is_blocking = True

        asyncio.ensure_future(self.receive_client(coro, name, is_blocking), loop=self.event_loop)
        self.active_coros[name] = coro

    def remove_service(self, name):
        """
        stop and remove client
        :return:
        """
        self.active_coros[name].cancel()

    def get_client(self, name):
        """
        get client from name
        :return:
        """
        if name not in self.active_services.keys():
            return Exception("Invalid Service Name")
        return self.active_coros[name].client

    async def receive_queue_coro(self):
        self.queue_listen_coro = self.master_queue.get()
        name, message = asyncio.wait_for(self.queue_listen_coro, loop = self.event_loop)
        self.active_services[name].on_message(message)

    async def receive_client(self, coro, name, is_blocking=False):
        while True:
            if is_blocking:
                message = asyncio.wait_for(coro, timeout=self.receive_timeout)
            else:
                message = await coro
            await self.master_queue.put((name, message))

    def __del__(self):
        if not self.master_queue.empty():
            print("******WARNING********", "Unread Messages Are Present")
        self.queue_listen_coro.cancel()

