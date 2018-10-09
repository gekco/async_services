class BaseAsyncServicesException(Exception):
    pass

class DuplicateServiceNameError(BaseAsyncServicesException):
    pass

class InvalidQueueMessage(BaseAsyncServicesException):
    pass