from webservices.settings            import MYLOGGER as logger


class BaseHandler(object):
    def __init__(self, name = 'Handler'):
        self.name = name

    def handleMessage(self, message):
        logger.info('Received Message From {0} : {1}'.format(self.name, message))