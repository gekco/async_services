import socket

import errno

from common.utils import log_exception


class BaseTransport(object):

    def __init__(self, host, port, name, connType, sock = None):
        self.host       = host
        self.port       = port
        self.name       = name
        self.socket     = sock
        self.connType   = connType

    def initConnection(self):
        pass

    def receive(self, bytesToReceive = -1):
        while True:
            try:
                if bytesToReceive == -1:
                    return self.socket.recv()
                else:
                    return self.socket.recv(bytesToReceive)
            except socket.error as e:
                log_exception(e)
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    time.sleep(1)
                    continue
                else:
                    break

    def send(self, message ):
        """Sends Messages over Established Connection"""
        try:
            logger = settings.MYLOGGER
            return self.socket.send( message )
        except Exception as e:
            log_exception(e)
            MYLOGGER.exception("Write to {0} {1} {2} {3} failed" .format(self.connType, self.name, self.host, self.port))
            raise e

    def close(self):
        if(self.socket is None):
            return
        MYLOGGER.info('{0} Connection Closed with {1} {2}:{3}'.format(self.connType, self.name, self.host, self.port))
        self.socket.close()
