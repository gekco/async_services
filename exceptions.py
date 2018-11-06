class BaseAsyncServicesException(Exception):
    pass

class DuplicateServiceNameError(BaseAsyncServicesException):
    pass

class InvalidQueueMessage(BaseAsyncServicesException):
    pass

class ReadTimeoutError(BaseAsyncServicesException):
    pass

class ConnectionClosed(BaseAsyncServicesException):
    pass

class SendFailed(BaseAsyncServicesException):
    pass