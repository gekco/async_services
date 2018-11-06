import asyncio
import logging
import threading

import functools
from inspect import iscoroutine, isawaitable

from async_services.exceptions import DuplicateServiceNameError, InvalidQueueMessage, ConnectionClosed, ReadTimeoutError
from common.utils import log_exception


class BaseService:
    context = { 'name' : '__main__' }

    def __init__(self, *args, **kwargs):
        pass

    def init_connection(self, *args, **kwargs):
        pass

    def read(self):
        '''
        single read for service
        :return: message recieved
        '''
        raise NotImplementedError("BaseService.read not Implemented")

    def send(self, message):
        raise NotImplementedError("BaseService.send not Implemented")

    def close(self, message):
        pass

class AsyncBaseService(BaseService):
    async def init_connection(self, *args, **kwargs):
        pass

    async def read(self):
        raise NotImplementedError("BaseService.read not Implemented")

    async def send(self, message):
        raise NotImplementedError("BaseService.send not Implemented")

class SyncBaseService(BaseService):
    host = None
    port = None

    def __init__(self, host = "", port=-1):
        if not self.host:
            self.host = host
        if not self.port:
            self.port = port

class BaseHandler:
    context = {'name' : '__main__'}

    def handle(self, message):
        logging.debug('''
        _____________________Message Received__________________ 
        From : {service}
        Message : {message}        
        _______________________________________________________
        '''.format(message = message, service = self.context['name']))

class BaseManager:
    services_classes = {}
    running_services = {}

    def run(self):
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError as e:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        self.queue = asyncio.Queue()

        for name,service_context in self.services_classes.items():
            self.add_service(name,
                             service_context["service"] ,
                             service_context.get("handler", BaseHandler),
                             service_context.get("on_call", False),
                             service_context.get("service_kwargs", dict()),
                             service_context.get("handler_kwargs", dict()),
                             True)

        self.loop.run_until_complete(self.read_queue())

    async def handle_message(self, name, message):
        try:
            response = self.running_services[name]["handler"].handle(message)
            if isawaitable(response):
                await response
        except Exception as e:
            log_exception(e)

    def send_message(self, name, message):
        new_message = dict(type="send", name=name, message=message)
        self.loop.call_soon_threadsafe(functools.partial(self.queue.put_nowait, new_message))

    async def close_service(self, name):
        self.running_services[name]["thread"].stop()
        self.running_services[name]["service"].close()

    async def start_service(self, name):
        if isinstance(self.running_services[name]["service"], SyncBaseService):
            thread = threading.Thread(target = self.read_service,name = name,
                                      args =(name, self.running_services[name]["service"]))
            self.running_services[name]["thread"] = thread
            thread.start()
        else:
            self.loop.call_soon(self.running_services[name]["service"].read())

    def add_service(self, name, service_class, handler_class, on_call, service_kwargs , handler_kwargs, is_already_added=False):
        if not is_already_added:
            if name not in self.services_classes.keys():
                self.services_classes[name] = {"service" : service_class, "handler" : handler_class,
                                          "on_call" : on_call, "service_kwargs" : service_kwargs,
                                          "handler_kwargs" : handler_kwargs}
            else:
                raise DuplicateServiceNameError("Service With This Name Already Exists")
        else:
            self.services_classes[name] = {"service": service_class, "handler": handler_class,
                                           "on_call": on_call, "service_kwargs": service_kwargs,
                                           "handler_kwargs": handler_kwargs}

        service = service_class(**service_kwargs)
        handler = handler_class(**handler_kwargs)
        handler.context = {"name" : name}
        service.context = {"name" : name}
        self.running_services[name] = {"handler" : handler, "service" : service}
        self.queue.put_nowait(dict(type="start", name=name))

    async def read_queue(self):
        while True:
            message = await self.queue.get()

            if "type" in message.keys():
                if message["type"] == "start":
                    await self.start_service(message["name"])
                elif message["type"] == "send":
                    self.running_services[message["name"]]["service"].send(message["message"])
                elif message["type"] == "close":
                    await self.close_service(message["name"])
                elif message["type"] == "received":
                    await self.handle_message(message["name"], message["message"])
                else:
                    logging.debug("""
                    __________ IGNORING MESSAGE _________
                    {message}
                    _____________________________________
                    """.format(message=message))
            else:
                raise InvalidQueueMessage("Message Does not have a 'type'")

    def get_service(self, name):
        return self.running_services[name]["service"]

    def read_service(self, name, service):
        while True:
            service.init_connection()
            if self.services_classes[name]["on_call"]:
                break
            while True:
                try:
                    message = service.read()
                    self.loop.call_soon_threadsafe(
                        functools.partial(self.queue.put_nowait,
                                          dict(type="received", name=name, message=message)))
                except ReadTimeoutError:
                    continue
                except ConnectionClosed:
                    break