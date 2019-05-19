import asyncio
from datetime import datetime

import pytest

from core import run_coro, service_manager, check_result, stop_manager, cancel_coro
from core.manager import CoroStatus


var=None

async def coroutine(seconds=1, raise_exception = False):
    await asyncio.sleep(seconds)
    if raise_exception:
        raise Exception("Sample Exception")
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
    def cb(result):
        global var
        print("inside callback", datetime.now(), var)
        var = result.split(" ")[0]

    coro_id = run_coro(coroutine(), callback=cb)
    result_flag, result = CoroStatus.Queued, None
    while result_flag == CoroStatus.Queued:
        result_flag, result = check_result(coro_id)
    assert var == "Hello"
    assert result_flag == CoroStatus.Completed


def test_cancel_coroutine():
    coro_id = run_coro(coroutine(1))
    cancel_coro(coro_id)
    result_flag, result = check_result(coro_id)
    assert result == None
    assert result_flag == CoroStatus.Cancelled


def test_timeout_coro():
    coro_id = run_coro(coroutine(5), timeout=1)
    result_flag, result = CoroStatus.Queued, None
    while result_flag == CoroStatus.Queued:
        result_flag, result = check_result(coro_id)
    assert result == None
    assert result_flag == CoroStatus.Timeout


def test_stop_manager():
    coro_id = run_coro(coroutine(5))
    stop_manager()
    test_blocked_coro()
    test_callback()
    stop_manager()