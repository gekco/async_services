Run fast asynchronous code from a synchronous code. Async Services provide a synchronous wrapper to run third party asynchronous code or any
coroutine for that matter in a synchronous way from a synchronous code.

Installation :

pip install async_services

Example Usage:
from async_services.core import run_coro

async def coroutine(seconds=1, raise_exception=False):
    await asyncio.sleep(seconds)
    if raise_exception:
        raise Exception("Sample Exception")
    return "Hello World"

result = run_coro(coroutine(), block=True)
print(result)
assert result[0] == CoroStatus.Completed
assert result[1] == "Hello World"

