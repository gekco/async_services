import asyncio
import uuid

import logging
from concurrent.futures import CancelledError

from async_services.core.exceptions import ManagerNotInitialized
from async_services.core.exceptions import CoroMissingException,\
    InvalidStateException


class Commands:
    Request = 0
    Response = 1


class CoroStatus:
    Queued = 0
    Completed = 1
    Failed = 2
    Cancelled = 3
    Timeout = 4


class ServiceManager:
    """
    class to manage connection
    """
    active_tasks = {}
    coros_result = {}
    master_queue = None
    queue_listen_task = None
    close = False
    event_loop = None
    is_initialized = False

    def run(self):
        try:
            self.event_loop = asyncio.get_event_loop()
        except Exception as e:
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

        self.active_tasks[coro_id] = False
        if callback and status == CoroStatus.Completed:
            try:
                callback(response)
            except Exception:
                self.coros_result[coro_id] = [CoroStatus.Failed, response]
        self.coros_result[coro_id] = [status, response]

    def schedule(self, coro, block=False, callback=None, timeout=None):
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

    def cancel_coro(self, coro_id, block=True, raise_exception=True):
        try:
            if self.coros_result[coro_id][0] == CoroStatus.Queued:

                task = self.active_tasks[coro_id]
                if not task:
                    if block:
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
        try:
            status, response = self.coros_result.get(coro_id)
            if status != CoroStatus.Queued:
                self.remove_coro(coro_id)
            return status, response
        except KeyError:
            raise CoroMissingException("Coroutine Id {}"
                                       " is not Active".format(coro_id))

    def stop(self):
        if not self.master_queue.empty():
            logging.warning("Unread Messages Are Present")
        for coro_id, coro in self.active_tasks.items():
            self.cancel_coro(coro_id, raise_exception=False)
        self.event_loop.call_soon_threadsafe(self.queue_listen_task.cancel)

    def remove_coro(self, coro_id):
        self.active_tasks.pop(coro_id, None)
        self.coros_result.pop(coro_id, None)
