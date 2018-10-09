import asyncio
import logging
import threading

from async_services.exceptions import DuplicateServiceNameError, InvalidQueueMessage


class BaseService:
    async def read(self):
        raise NotImplementedError("BaseService.read not Implemented")
    def send(self, message):
        raise NotImplementedError("BaseService.read not Implemented")


class BaseHandler:
    context = {'name' : '__main__'}

    def handle(self, message):
        logging.info('''
        _____________________Message Received__________________ 
        From : {service}
        Message : {message}        _______________________________________________________
        '''.format(message = message, service = self.context['name']))

class BaseManager(threading.Thread):
    services_classes = {}
    running_services = {}
    queue = asyncio.Queue()

    def run(self):
        try:
            self.loop = asyncio.get_event_loop()
        except Exception:
            self.loop = asyncio.new_event_loop()

        self.loop.call_soon(self.read_queue())

        for name,service_context in self.services_classes.items():
            self.add_service(name,
                             service_context["service"] ,
                             service_context["handler"],
                             service_context.get("on_call", False),
                             service_context.get("service_kwargs", None),
                             service_context.get("handler_kwargs", None),
                             True)

    def send_message(self, name, message):
        new_message = dict(type="send", message=message)
        self.queue.put_nowait(new_message)

    async def close_service(self, name):
        self.running_services[name]["coro"].cancel()

    async def start_service(self, name):
        self.loop.call_soon(self.running_services[name]["coro"])

    def add_service(self, name, service_class, handler_class, on_call, service_kwargs, handler_kwargs, is_already_added=False):
        if not is_already_added:
            if name not in self.services_classes.keys():
                self.services_classes[name] = {"service" : service_class, "handler" : handler_class,
                                          "on_call" : on_call, "service_kwargs" : service_kwargs,
                                          "handler_kwargs" : handler_kwargs}
            else:
                raise DuplicateServiceNameError("Service With This Name Already Exists")

        service = service_class(**service_kwargs)
        handler = handler_class(**handler_kwargs)
        handler.context = {"name" : name}
        self.running_services[name] = {"handler" : handler, "coro" : service.read(), "service" : service}
        self.queue.put_nowait(dict(type="start", message=dict(name=name)))

    async def read_queue(self):
        message = await self.queue.get()
        if "type" in message.keys():
            if message["type"] == "start":
                await self.start_service(message["name"])
            elif message["type"] == "send":
                self.running_services[message["name"]]["service"].send(message["message"])
            elif message["type"] == "close":
                await self.close_service(message["name"])
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
