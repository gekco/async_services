# Async Services

Run fast asynchronous code from a synchronous code. Async Services provide a synchronous wrapper to run
third party asynchronous code or any coroutine for that matter in a synchronous way from a synchronous code.

### Installation

```
pip install async_services
```

## For Development Purposes
Install project Dependencies
```
pip install -r requirements.txt
```

```
pip install -U .
```

## Running the tests

You can run the tests with the following command

```
pytest .
```

### And coding style tests

```
pycodestyle .
```

### Example Usage

```
from async_services.core import run_coro
import asyncio

async def coroutine(seconds=1, raise_exception=False):
    await asyncio.sleep(seconds)
    if raise_exception:
        raise Exception("Sample Exception")
    return "Hello World"

run_manager()
result = run_coro(coroutine(), block=True)
print(result)
assert result[0] == CoroStatus.Completed
assert result[1] == "Hello World"
stop_manager()

```

## Authors

* **Ankit Kathuria** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone whose code was used
* Inspiration
* etc


