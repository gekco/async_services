import threading

from async_services.core.exceptions import ManagerNotInitialized
from async_services.core.manager import ServiceManager


# There will be only one Service Manager at a time
# The Service Manager can be Stopped at any point of time
service_manager = None


def run_manager(block=False):
    """
    Starts the manager process

    You need not call this function before scheduling a
    coroutine. The scheduler will call it for you if not
    called before scheduling.

    :param block: if True this will be a blocking call
                  the event loop will run in the calling
                  thread. Otherwise a thread is spawned
                  for event loop to run.
    :return:
    """
    global service_manager
    if not service_manager:
        service_manager = ServiceManager()
        if block:
            service_manager.run()
        else:
            threading.Thread(target=service_manager.run).start()
            while not service_manager.is_initialized:
                pass


def run_coro(coro, block=False, callback=None, timeout=None):
    """

    :param coro: coroutine to schedule
    :param block: whether or not to block until the coroutine finishes
    :param callback: a function which at least takes two arguments
                     1. status : status of coroutine
                     2. response : value returned by the coroutine
    :param timeout:  Seconds after which coro is cancelled if
                     coroutine is not Completed
    :return: if block is True
                it returns a tuple <status, response>
            otherwise
                it returns a string <coruotine_id> that you
                can use to get the result in future
                or cancel it.
    """
    if not service_manager:
        run_manager()
    return service_manager.schedule(coro, block, callback, timeout)


def check_result(coro_id):
    """
    :param coro_id: corutine_id of the coroutine
    :return: it returns a tuple <status, response>
    """
    if service_manager:
        return service_manager.check_result(coro_id)
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")


def cancel_coro(coro_id):
    """
    :param coro_id: corutine_id of the coroutine
    :return:
    """
    if service_manager:
        return service_manager.cancel_coro(coro_id)
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")


def stop_manager():
    """
    Cancel all running coroutines. Close the thread.
    Stop Currently Running Manager
    :return:
    """
    global service_manager
    if service_manager:
        service_manager.stop()
        service_manager = None
        return
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")
