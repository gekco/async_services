import time

from base.clients import BaseClient, BaseAsyncClient
import asyncio

from common.utils import log_exception
from mdInterface.transports import AsyncRabbitMqTransport, MultiCastTransport
from webservices.settings import MYLOGGER

class GenericClient(BaseClient):
    ''' Base Client Class '''
    name = "Generic Client"
    def __init__(self, transport):
        self.transport = transport

    def buildConnection(self):
        return self.transport.initConnection()

    def receive(self):

        while (not self.buildConnection()):
            # retry after 1 second
            time.sleep(5)

        while True:
            try:
                message = self.transport.receive()
                if not message :
                    break
                return message
            except Exception as e:
                log_exception(e)

        MYLOGGER.info('CLOSING CONNECTION WITH {0} DMS'.format(self.name))
        self.close()


    def send(self, message):
        try:
            return self.transport.send(message)
        except Exception as e:
            log_exception(e)
            MYLOGGER.debug( 'Exception occured During sending a message to {0} '.format(self.name) )
            raise e

    def close(self):
        self.transport.close()


class GenericBaseAsyncClient(BaseAsyncClient):
    name = "Generic Async Client"

    def __init__(self, transport):
        self.transport = transport

    async def receive(self):
        while True:
            while (not await self.buildConnection()):
                # retry after 1 second
                asyncio.sleep(2)
            await self.transport.receive()

    async def buildConnection(self):
        return await self.transport.initConnection()


class TCPClient(GenericClient):
    transport=TCPTransport


class AsyncTCPClient(GenericBaseAsyncClient):
    transport = AsyncTCPTransport

class ZmqClient(GenericClient):
    transport = ZmqTransport


class AsyncRabbitMqClient(GenericBaseAsyncClient):
    ''' Client For Rabbit Mq'''
    transport = AsyncRabbitMqTransport

    def __init__(self, host, port, name, queueName = '', exchangeName = None, createQueue = False):
        '''
        initializes the Rabbit MQ Connection
        '''
        transport = self.transport(host, port, name, queueName, exchangeName, createQueue)

    async def receive(self):
        await self.transport.initConnection()
        MYLOGGER.info(
            ' {0} Waiting for Message at {1} : {2} Queue: {3} Exchange : {4}'.format(self.name, self.transport.host,
                                                                                     self.transport.port,
                                                                                     self.transport.queue_name,
                                                                                     self.transport.exchange_name))

        async for message in self.transport.queue:
            with message.process():
                MYLOGGER.debug("+++++++++++++++++++++++++++++++++MESAGE RECEIVED++++++++++++++++++++++++++++++++++++++++ {0}".format(message.body))
                yield message.body


class MultiCastClient(GenericBaseAsyncClient):
    transport = MultiCastTransport
    def __init__(self, host, port, ip, handler, serializer, name):
        '''
        initializes the Rabbit MQ Connection
        '''
        transport = self.transport_class(host, port,ip, name)
        super().__init__(transport, handler, serializer, appendIfNotNone(name , 'Multicast Client'))


    async def receive(self):
        while True:
            try:
                msgBody = await self.transport.receive()

                if not msgBody:
                    break

                return msgBody
            except Exception as e:
                log_exception(e)

        self.close()