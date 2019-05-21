import asyncio
import traceback
import uuid

import logging
from concurrent.futures import CancelledError

from async_services.core.exceptions import ManagerNotInitialized, DemoException
from async_services.core.exceptions import CoroMissingException,\
    InvalidStateException


class CoroStatus:
    """
    Queued = 0                   -> Coroutine is still queued waiting
                                    to be executed or is being executed
    Completed = 1                -> Coroutine has Completed Successfully
    Failed = 2                   -> Coroutine Completed Successfully,
                                    But callback function raised an exception
    Cancelled = 3                -> Coroutine was Cancelled
    Timeout = 4                  -> Coroutine did not complete in the given
                                    time
    CoroutineException = 5       -> Coroutine Itself Raised an Exception
    """
    Queued = 0
    Completed = 1
    Failed = 2
    Cancelled = 3
    Timeout = 4
    CoroutineException = 5


class ServiceManager:
    """
    Manager Class to manage all the asynchronus tasks

    active_tasks       -> Map of coroutine_id vs Task object
    coros_result       -> Map of coroutine_id vs Tuple(status, result)
    master_queue       -> Asynchronus master queue in which all the
                          tasks are pushed before scheduling
    queue_listen_task  -> Task that continously listens to
                          queue and process the tasks
    event_loop         -> Current event loop

    """
    active_tasks = None
    coros_result = None
    master_queue = None
    queue_listen_task = None
    event_loop = None
    is_initialized = False

    def run(self):
        """
        A Blocking function which
        1. Initialize the event loop
        2. Initialize the queue
        3. Listen to the queue in the event loop
        :return:
        """
        self.active_tasks, self.coros_result = {}, {}
        try:
            self.event_loop = asyncio.get_event_loop()
        except Exception:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
        self.master_queue = asyncio.Queue()
        self.queue_listen_task = asyncio.Task(self.receive_queue_coro())
        self.is_initialized = True
        try:
            self.get_event_loop().run_until_complete(self.queue_listen_task)
        except CancelledError:
            logging.debug("Closing the Thread.")

    def get_event_loop(self):
        if not self.event_loop:
            raise ManagerNotInitialized("Manager is not Initialized Yet.")
        return self.event_loop

    async def receive_queue_coro(self):
        while True:
            coro_id, coro, callback, timeout = await self.master_queue.get()
            asyncio.ensure_future(
                self.start_coro(coro_id, coro, callback, timeout))

    async def start_coro(self, coro_id, coro, callback, timeout):
        """
        :param coro_id: Coruotine Id
        :param coro: Coroutine to be executed
        :param callback: Function to be called
        :param timeout:

        Execute task and update the corresponding maps
        :return:
        """
        try:
            task = asyncio.Task(coro)
            self.active_tasks[coro_id] = task
            response = await asyncio.wait_for(task, timeout,
                                              loop=self.event_loop)
            status = CoroStatus.Completed
        except asyncio.TimeoutError:
            self.coros_result[coro_id][0] = CoroStatus.Timeout
            response = None
            status = CoroStatus.Timeout
        except CancelledError:
            self.coros_result[coro_id][0] = CoroStatus.Cancelled
            response = None
            status = CoroStatus.Cancelled
        except Exception as e:
            print(e, type(e))
            if not isinstance(e, DemoException):
                traceback.print_tb(e.__traceback__)
            self.coros_result[coro_id][0] = CoroStatus.CoroutineException
            response = None
            status = CoroStatus.CoroutineException

        self.active_tasks[coro_id] = False
        if callback:
            try:
                callback(status, response)
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                self.coros_result[coro_id] = [CoroStatus.Failed, response]
        self.coros_result[coro_id] = [status, response]

    def schedule(self, coro, block=False, callback=None, timeout=None):
        """
        Schedule Coroutine

        :param coro:
        :param block:
        :param callback:
        :param timeout:
        :return:   if block is False it returns coro_id
                   otherwise reutrn (status, result)

        """
        coro_id = str(uuid.uuid4())
        self.get_event_loop().call_soon_threadsafe(
            self.master_queue.put_nowait, [coro_id, coro, callback, timeout])
        self.coros_result[coro_id] = [CoroStatus.Queued, None]
        self.active_tasks[coro_id] = False
        if block:
            status, result = self.check_result(coro_id)
            while status == CoroStatus.Queued:
                status, result = self.check_result(coro_id)
            return status, result
        return coro_id

    def cancel_coro(self, coro_id, raise_exception=True):
        """
        Cancel the scheduled Coroutine
        :param coro_id: Coroutine Id
        :param raise_exception: whether to raise an Exception
                or not if coroutine is  already cancelled
        :return:
        """
        try:
            if self.coros_result[coro_id][0] == CoroStatus.Queued:
                task = self.active_tasks[coro_id]
                if not task:
                    while not task:
                        task = self.active_tasks[coro_id]
                if task:
                    self.event_loop.call_soon_threadsafe(task.cancel)
                self.active_tasks[coro_id] = False
                self.coros_result[coro_id][0] = CoroStatus.Cancelled
            else:
                if raise_exception:
                    raise InvalidStateException(
                        "Cannot Cancel a Coroutine."
                        "Coruotine is Already Finished.")
        except KeyError:
            raise CoroMissingException("Coroutine Id {}"
                                       " is not Active".format(coro_id))

    def check_result(self, coro_id):
        """
        Check result of a Coroutine
        :param coro_id: Coroutine id
        :return:
        """
        try:
            status, response = self.coros_result.get(coro_id)
            if status != CoroStatus.Queued:
                self.remove_coro(coro_id)
            return status, response
        except KeyError:
            raise CoroMissingException("Coroutine Id {}"
                                       " is not Active".format(coro_id))

    def stop(self):
        """
        Stop the manager
        :return:
        """
        if not self.master_queue.empty():
            logging.warning("Unread Messages Are Present")
        for coro_id, coro in self.active_tasks.items():
            self.cancel_coro(coro_id, raise_exception=False)
        self.event_loop.call_soon_threadsafe(self.queue_listen_task.cancel)

    def remove_coro(self, coro_id):
        """
        Remove Coroutine from maps
        :param coro_id:
        :return:
        """
        self.active_tasks.pop(coro_id, None)
        self.coros_result.pop(coro_id, None)
