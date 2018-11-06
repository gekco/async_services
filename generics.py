import logging
import socket

import errno
import struct

import grpc
import zmq

import services_pb2_grpc
from async_services.base import SyncBaseService
from async_services.exceptions import ReadTimeoutError, ConnectionClosed, SendFailed


class TCPService(SyncBaseService):
    host = None
    port = None
    recv_size = 1024

    def init_connection(self, *args, **kwargs):
        self.socket        = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address     = ( self.host, self.port )
        self.socket.connect( server_address )
        logging.info('Established TCP Connection With {0} {1}:{2} Successfully'.
                     format(self.context["name"], self.host, self.port))
        return True

    def read(self):
        try:
            return self.socket.recv(self.recv_size)
        except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    raise ReadTimeoutError("Timeout Error while receiving")
                else:
                    raise ConnectionClosed("Connection Closed")

    def send(self, message ):
        """Sends Messages over Established Connection"""
        try:
            return self.socket.send( message )
        except socket.error as e:
            logging.exception("Write to {0} {1} {2} failed" .format(self.context["name"], self.host, self.port))
            raise SendFailed("Send To TCP Socket Failed")

    def close(self):
        if(self.socket is None):
            return
        self.socket.close()

class ZMQService(SyncBaseService):

    def init_connection(self):
        "initializes the connection"
        context = zmq.Context()
        self.socket  = context.socket( zmq.SUB )
        self.socket.connect( "tcp://{0}:{1}".format(self.host, self.port) )
        self.socket.setsockopt_string( zmq.SUBSCRIBE, "" )
        logging.info("Connection Established Successfully {0} {1}:{2}".format(self.context["name"],
                                                                              self.host, self.port))
        return True

    def read(self):
        try:
            return self.socket.recv()
        except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    raise ReadTimeoutError("Timeout Error while receiving")
                else:
                    raise ConnectionClosed("Zmq Connection Closed")


class GRPCService(SyncBaseService):

    def init_connection(self):
        self.channel  = grpc.insecure_channel('{0}:{1}'.format(self.host, self.port))
        self.stub     = services_pb2_grpc.RpcServiceStub(self.channel)

        logging.info("Connection Established Successfully With {0} {1}:{2}".
                         format(self.context["name"], self.host, self.port))


class MulticastService(SyncBaseService):
    host = None
    port = None
    ip = None

    def __init__(self, host="", port=-1, ip=""):
        self.tries = 0
        self.multicast_group = host if not self.host else self.host
        self.multicast_ip = ip if not self.ip else self.ip
        self.server_address = (host, port)

    def init_connection(self):
        self.tries         = self.tries + 1
        self.socket = socket.socket(socket.AF_INET,
                                    socket.SOCK_DGRAM,
                                    socket.IPPROTO_UDP)
        self.broadcast_group = socket.inet_aton(self.multicast_group)

        self.interface_ip = socket.inet_aton(self.multicast_ip)

        self.multicast_request = struct.pack('=4s4s',
                                             self.broadcast_group,
                                             self.interface_ip)

        self.socket.setsockopt(socket.SOL_SOCKET,
                               socket.SO_REUSEADDR,
                               1)

        self.socket.bind(('', self.port))

        logging.info('Established UDP Multicast Connection With {0} {1}:{2} Successfully'.format(self.context["name"], self.host, self.port))
        self.tries = 1

        return True

    def read(self):
        while True:
            try:
                data = self.socket.recv(4096)
                return data
            except socket.error as e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    raise ReadTimeoutError("Timeout Error while receiving")
                else:
                    raise ConnectionClosed("Connection Closed")
