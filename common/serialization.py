'''
This File Contains functions that Handles the serialization and deserialization of the Proto buf structure messages
'''
import socket

from webservices.settings import  MYLOGGER as logger
from threading            import current_thread

def SerializeProtoMsg(obj, printLogs = True):
    if printLogs:
        logger.info('''
    ------------------------SENDING TO BACKEND--------------------------------------
    THREAD : {0}
    DATA   : {1}
    --------------------------------------------------------------------------------
    '''.format(current_thread(), obj))
    serializedString = obj.SerializeToString()
    return serializedString

def DeSerializeProtoMsg(obj,serializedString, printLogs = True):
    obj.ParseFromString(serializedString)
    if printLogs:
        logger.info('''
            ------------------------RECEIVED FROM BACKEND-----------------------------------
            THREAD : {0}
            DATA   : {1}
            --------------------------------------------------------------------------------
            '''.format(current_thread(), obj))
    return obj


def ntohl(n):
    return socket.ntohl(n & 0xffffffff)

def htonl(n):
    return socket.htonl(n & 0xffffffff)


