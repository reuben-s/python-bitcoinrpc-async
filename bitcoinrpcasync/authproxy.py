
"""
  Copyright 2023 Reuben S

  python-bitcoinrpc-async adds asyncronous functionality to the AuthServiceProxy. 
  Includes asyncio compatible methods for making and handling requests, 
  making it easy to integrate into your codebase. 
  You can now take advantage of the benefits of asynchronous programming, using 
  the modern async and await syntax. 

  Previous copyright, from python-bitcoinrpc/bitcoinrpc/authproxy.py:

  Copyright 2011 Jeff Garzik

  AuthServiceProxy has the following improvements over python-jsonrpc's
  ServiceProxy class:

  - HTTP connections persist for the life of the AuthServiceProxy object
    (if server supports HTTP/1.1)
  - sends protocol 'version', per JSON-RPC 1.1
  - sends proper, incrementing 'id'
  - sends Basic HTTP authentication headers
  - parses all JSON numbers that look like floats as Decimal
  - uses standard Python json lib

  Previous copyright, from python-jsonrpc/jsonrpc/proxy.py:

  Copyright (c) 2007 Jan-Klaas Kollhof

  This file is part of jsonrpc.

  jsonrpc is free software; you can redistribute it and/or modify
  it under the terms of the GNU Lesser General Public License as published by
  the Free Software Foundation; either version 2.1 of the License, or
  (at your option) any later version.

  This software is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public License
  along with this software; if not, write to the Free Software
  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

from __future__ import annotations

import decimal
import json
from logging import Logger, getLogger
from types import TracebackType
import urllib.parse as urlparse

from typing import (
    Dict, 
    List,
    Callable,
    Tuple,
    Optional,
    Type,
    Any
)

from aiohttp import (
    ClientSession,
    ClientResponse,
    BasicAuth,
    TCPConnector,
    ClientTimeout
)

USER_AGENT: str = "AuthServiceProxy/0.1"

HTTP_TIMEOUT: int = 30

log: Logger = getLogger("BitcoinRPC")

class JSONRPCException(Exception):
    def __init__(
        self, 
        rpc_error: Dict[str, Any]
        ) -> None:
        parent_args: List[Dict[str, Any]] = []
        try:
            parent_args.append(rpc_error["message"])
        except:
            pass
        Exception.__init__(self, *parent_args)
        self.error: Dict[str, Any] = rpc_error
        self.code: int = rpc_error["code"] if "code" in rpc_error else None
        self.message: str = rpc_error["message"] if "message" in rpc_error else None

    def __str__(self) -> str:
        return f"s{self.code}: {self.message}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self}'>"

def EncodeDecimal(o: Callable[[Any], Any]) -> float:
    if isinstance(o, decimal.Decimal):
        return float(round(o, 8))
    raise TypeError(repr(o) + " is not JSON serializable")

class AuthServiceProxy:
    __id_count: int = 0
 
    def __init__(
        self, 
        service_url: str, 
        service_name: str = None, 
        timeout:int = 0, 
        connection: ClientSession = None,
        ssl_context: Any = None
        ) -> None:
        self.__service_url: str = service_url
        self.__service_name: str = service_name
        self.__url: urlparse.ParseResult = urlparse.urlparse(service_url)

        self.__timeout: int = timeout

        if connection:
            # Callables re-use the connection of the original proxy
            self.__conn: ClientSession = connection
        elif self.__url.scheme == "https":
            self.__conn: ClientSession = ClientSession(
                timeout = ClientTimeout(total = self.__timeout),
                connector = TCPConnector(ssl = ssl_context)
            )
        else:
            self.__conn: ClientSession = ClientSession(
                timeout = ClientTimeout(total = self.__timeout)
            )

    async def __aenter__(self) -> AuthServiceProxy:
        return self

    async def __aexit__(
        self, 
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        traceback: Optional[TracebackType]
        ) -> None:
        if self.__conn:
            await self.__conn.__aexit__(exc_type, exc_val, traceback)

    async def close(self) -> None:
        await self.__conn.close()

    def __getattr__(
        self, 
        name: str
        ) -> AuthServiceProxy:
        if name.startswith("__") and name.endswith("__"):
            # Python internal stuff
            raise AttributeError
        if self.__service_name is not None:
            name = f"{self.__service_name}.{name}"

        return AuthServiceProxy(self.__service_url, name, self.__timeout, self.__conn)

    async def __call__(
        self, 
        *args: Tuple[Any, ...]
        ) -> Any:
        AuthServiceProxy.__id_count += 1

        log.debug(f"-{AuthServiceProxy.__id_count}-> {self.__service_name} {json.dumps(args, default=EncodeDecimal)}")

        response: ClientResponse = await self._post(
            {
                "version": "1.1",
                "method": self.__service_name,
                "params": args,
                "id": AuthServiceProxy.__id_count
            }
        )

        parsed_response: Dict[str, Any] = await self._parse_response(response)

        if parsed_response.get("error") is not None:
            raise JSONRPCException(parsed_response["error"])
        elif "result" not in parsed_response:
            raise JSONRPCException({"code": -343, "message": "missing JSON-RPC result"})
            
        return parsed_response["result"]

    async def batch_(
        self, 
        rpc_calls: List[List[Any]]
        ) -> List[Any]:
        """Batch RPC call.
           Pass array of arrays: [ [ "method", params... ], ... ]
           Returns array of results.
        """
        batch_data: Dict[Any] = []
        for rpc_call in rpc_calls:
            AuthServiceProxy.__id_count += 1
            method: str = rpc_call.pop(0)
            batch_data.append(
                {
                    "jsonrpc": "2.0", 
                    "method": method, 
                    "params": rpc_call, 
                    "id": AuthServiceProxy.__id_count
                }
            )

        log.debug(f"--> {batch_data}")

        response: ClientResponse = await self._post(batch_data)

        responses: Dict[str, Any] = await self._parse_response(response)
        results: List[Any] = []

        if isinstance(responses, (dict,)):
            if ("error" in responses) and (responses["error"] is not None):
                raise JSONRPCException(responses["error"])
            raise JSONRPCException(
                {
                    "code": -32700, 
                    "message": "Parse error"
                }
            )

        for response in responses:
            if response["error"] is not None:
                raise JSONRPCException(response["error"])
            elif "result" not in response:
                raise JSONRPCException(
                    {
                        "code": -343, 
                        "message": "missing JSON-RPC result"
                    }
                )
            else:
                results.append(response["result"])

        return results

    async def _post(
        self, 
        data: Dict[str, Any]
        ) -> ClientResponse:
        postdata: str = json.dumps(data, default=EncodeDecimal)

        log.debug(f"-{AuthServiceProxy.__id_count}-> {self.__service_name} {postdata}")

        response: ClientResponse = await self.__conn.post(
            f"http://{self.__url.hostname}:{self.__url.port}",
            auth = BasicAuth(self.__url.username, self.__url.password), 
            data = postdata,
            headers = {
                "Host": self.__url.hostname,
                "User-Agent": USER_AGENT,
                "Content-type": "application/json"
            }
        )
        return response

    async def _parse_response(
        self, 
        response: ClientResponse
        ) -> Dict[str, Any]:
        content_type: str = response.headers["Content-Type"]
        if content_type != "application/json":
            raise JSONRPCException(
                { 
                    "code": -342, 
                    "message": f"non-JSON HTTP response with '{response.status} {response.reason}' from server"
                }
            )

        text: str = await response.text()
        response_json: Dict[str, Any] = json.loads(text, parse_float=decimal.Decimal)

        if "error" in response_json and response_json["error"] is None:
            log.debug(f"<-{response_json['id']}- {response_json}")
        else:
            log.debug(f"<-- {response_json}")

        return response_json
