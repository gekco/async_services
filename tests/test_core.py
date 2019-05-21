import asyncio
from datetime import datetime

import pytest

from async_services.core import run_coro, check_result, \
    stop_manager, cancel_coro, run_manager
from async_services.core.exceptions import DemoException
from async_services.core.manager import CoroStatus


var = None
callback_count = 3


@pytest.fixture(autouse=True)
def manager_start_stope():
    run_manager()
    yield
    stop_manager()


async def coroutine(seconds=1, raise_exception=False):
    await asyncio.sleep(seconds)
    if raise_exception:
        raise DemoException("Sample Exception")
    return "Hello World"


def test_blocked_coro():
    result = run_coro(coroutine(), block=True)
    assert result[0] == CoroStatus.Completed
    assert result[1] == "Hello World"


def test_unblocked_async_coro():
    coro_id = run_coro(coroutine())
    result_flag, result = CoroStatus.Queued, None
    while result_flag == CoroStatus.Queued:
        result_flag, result = check_result(coro_id)
    assert result == "Hello World"
    assert result_flag == CoroStatus.Completed


def test_callback():
    def cb(result_flag, result_coro):
        global var, callback_count
        if (result_flag == CoroStatus.Completed):
            if not var:
                var = result_coro
            var = var[callback_count:]
            callback_count -= 1
            if callback_count:
                run_coro(coroutine(), callback=cb)

    run_coro(coroutine(), callback=cb)

    while callback_count:
        pass
    assert var == "World"


def test_cancel_coroutine():
    coro_id = run_coro(coroutine(1))
    cancel_coro(coro_id)
    result_flag, result = check_result(coro_id)
    assert result is None
    assert result_flag == CoroStatus.Cancelled


def test_timeout_coro():
    coro_id = run_coro(coroutine(5), timeout=1)
    result_flag, result = CoroStatus.Queued, None
    while result_flag == CoroStatus.Queued:
        result_flag, result = check_result(coro_id)
    assert result is None
    assert result_flag == CoroStatus.Timeout


def test_coro_raise_exception():
    result = run_coro(coroutine(raise_exception=True), block=True)
    assert result[0] == CoroStatus.CoroutineException
