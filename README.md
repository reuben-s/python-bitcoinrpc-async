# python-bitcoinrpc-async

python-bitcoinrpc-async adds asyncronous functionality to the AuthServiceProxy. It includes asyncio compatible methods for making and handling requests, making it easy to integrate into your codebase. With python-bitcoin-rpc you can now take advantage of the benefits of asynchronous programming, using the modern `async` and `await` syntax. 

## AuthServiceProxy

AuthServiceProxy is an asyncio compatible version of python-bitcoinrpc.

It includes the following features:

- Asynchronous context manager for performing asyncronous HTTP requests
- HTTP connections persist for the life of the AuthServiceProxy object
- sends protocol 'version', per JSON-RPC 1.1
- sends proper, incrementing 'id'
- uses standard Python json lib
- can optionally log all RPC calls and results
- JSON-2.0 batch support

It also includes the following bitcoin-specific details:

- sends Basic HTTP authentication headers
- parses all JSON numbers that look like floats as Decimal, and serializes Decimal values to JSON-RPC connections.

## Installation

```
pip install python-bitcoinrpc-async
```

## Example
```python
from bitcoinrpcasync import AuthServiceProxy
import asyncio

async def main():
    async with AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332") as rpc_connection:
        best_block_hash = await rpc_connection.getbestblockhash()
        print(best_block_hash)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

## Batch support
```python
from bitcoinrpcasync import AuthServiceProxy
import asyncio

async def main():
    async with AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332") as rpc_connection:
        commands = [["getblockhash", height] for height in range(100)]
        block_hashes = await rpc_connection.batch_(commands)
        blocks = await rpc_connection.batch_([["getblock", h] for h in block_hashes])
        block_times = [block["time"] for block in blocks]
        print(block_times)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

## Logging all RPC calls to stderr

```python
from bitcoinrpcasync import AuthServiceProxy
import logging
import asyncio

logging.basicConfig()
logging.getLogger("BitcoinRPC").setLevel(logging.DEBUG)

async def main():
    async with AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332") as rpc_connection:
        info = await rpc_connection.getinfo()
        print(info)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

```

Produces output on stderr like

```
DEBUG:BitcoinRPC:-1-> getinfo []
DEBUG:BitcoinRPC:<-1- {"connections": 8, ...etc }
```

## Socket timeouts under heavy load
Pass the timeout argument to prevent "socket timed out" exceptions:

```python
AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332", timeout=120)
```

## SSL/TLS connections
To set up a SSL/TLS connection pass a `ssl.SSLContext` object into the ssl_context argument of the `AuthServiceProxy`:
```python
AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332", ssl_context=ssl.create_default_context())
```
