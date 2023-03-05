# python-bitcoinrpc-async

python-bitcoinrpc-async adds asyncronous functionality to the AuthServiceProxy. It includes asyncio compatible methods for making and handling requests, making it easy to integrate into your codebase. With python-bitcoin-rpc you can now take advantage of the benefits of asynchronous programming, using the modern `async` and `await` syntax. 

## AuthServiceProxy

AuthServiceProxy is an asyncio compatible version of python-bitcoinrpc.

It includes the following features:

- Asynchronous context manager for performing asyncronous HTTP requests
- HTTP connections persist for the life of the AuthServiceProxy object
- sends protocol 'version', per JSON-RPC 1.1
- sends proper, incrementing 'id'
- can optionally log all RPC calls and results
- JSON-2.0 batch support (Not yet supported)

It also includes the following bitcoin-specific details:

- sends Basic HTTP authentication headers
- parses all JSON numbers that look like floats as Decimal,
  and serializes Decimal values to JSON-RPC connections. (Not yet supported)

## Installation

```
pip install python-bitcoinrpc-async
```

## Example

```python
from bitcoinrpcasync.authproxy import AuthServiceProxy, JSONRPCException
import asyncio
    
async def main():
    # rpc_user and rpc_password are set in the bitcoin.conf file
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332")
    best_block_hash = await rpc_connection.getbestblockhash()
    print(best_block_hash)
    await rpc_connection.close()
      
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

## Example using context manager
```python
from bitcoinrpcasync.authproxy import AuthServiceProxy, JSONRPCException
import asyncio

async def main():
    async with AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332") as rpc_connection:
        best_block_hash = await rpc_connection.getbestblockhash()
        print(best_block_hash)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
```

## Logging all RPC calls to stderr

```python
from bitcoinrpcasync.authproxy import AuthServiceProxy, JSONRPCException
import logging
import asyncio

logging.basicConfig()
logging.getLogger("BitcoinRPC").setLevel(logging.DEBUG)

async def main():
    rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332")
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
rpc_connection = AuthServiceProxy(f"http://{rpc_user}:{rpc_password}@127.0.0.1:8332", timeout=120)
```
