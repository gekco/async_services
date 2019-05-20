import threading

from async_services.core.exceptions import ManagerNotInitialized
from async_services.core.manager import ServiceManager


service_manager = None


def run_manager(block=False):
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
    if not service_manager:
        run_manager()
    return service_manager.schedule(coro, block, callback, timeout)


def check_result(coro_id):
    if service_manager:
        return service_manager.check_result(coro_id)
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")


def cancel_coro(coro_id):
    if service_manager:
        return service_manager.cancel_coro(coro_id)
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")


def stop_manager():
    global service_manager
    if service_manager:
        service_manager.stop()
        service_manager = None
        return
    raise ManagerNotInitialized("Async Services Manager Not Initialized.")
