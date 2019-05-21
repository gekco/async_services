class CoroMissingException(Exception):
    """
    Coroutine is Missing . Raised if try to cancel
     or check the status of a coroutine which is not yet scheduled.
    """
    pass


class InvalidStateException(Exception):
    """
    Raised When a Coroutine is Finished yet an attempt to
    cancel is made.
    """
    pass


class ManagerNotInitialized(Exception):
    """
    Manager is not initialized and you try to
    cancel a corutine or check its status.
    """
    pass


class DemoException(Exception):
    """Demo Test Exception"""
    pass
