
class BaseClient(object):
    ''' Abstarct Base Client Class '''

    def receive(self):
        """
        :return: message received
        """
        raise NotImplemented("Receive Not Implemented")



class BaseAsyncClient(BaseClient):

    async def receive(self):
        """
        :return: message received
        """
        raise NotImplemented("Receive Not Implemented")