
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

import decimal
import json
import logging
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

# async port
import aiohttp
import asyncio

USER_AGENT = "AuthServiceProxy/0.1"

HTTP_TIMEOUT = 30

log = logging.getLogger("BitcoinRPC")

class JSONRPCException(Exception):
    def __init__(self, rpc_error):
        parent_args = []
        try:
            parent_args.append(rpc_error['message'])
        except:
            pass
        Exception.__init__(self, *parent_args)
        self.error = rpc_error
        self.code = rpc_error['code'] if 'code' in rpc_error else None
        self.message = rpc_error['message'] if 'message' in rpc_error else None

    def __str__(self):
        return '%d: %s' % (self.code, self.message)

    def __repr__(self):
        return '<%s \'%s\'>' % (self.__class__.__name__, self)

def EncodeDecimal(o):
    if isinstance(o, decimal.Decimal):
        return float(round(o, 8))
    raise TypeError(repr(o) + " is not JSON serializable")

class AuthServiceProxy(object):
    __id_count = 0
 
    def __init__(self, service_url, service_name=None, timeout=HTTP_TIMEOUT, 
                 connection=None, ssl_context=None):
        self.__service_url = service_url
        self.__service_name = service_name
        self.__url = urlparse.urlparse(service_url)
        if self.__url.port is None:
            port = 80
        else:
            port = self.__url.port

        self.__timeout = timeout

        if connection:
            # Callables re-use the connection of the original proxy
            self.__conn = connection
        else:
            t = aiohttp.ClientTimeout(total=self.__timeout)
            self.__conn = aiohttp.ClientSession(timeout=t)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, traceback):
        if self.__conn:
            await self.__conn.close()
            self.__conn = None

    async def close(self):
        await self.__conn.close()

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            # Python internal stuff
            raise AttributeError
        if self.__service_name is not None:
            name = "%s.%s" % (self.__service_name, name)
        return AuthServiceProxy(self.__service_url, name, self.__timeout, self.__conn)

    async def __call__(self, *args):
        AuthServiceProxy.__id_count += 1

        response = await self._post(
            {
                'version': '1.1',
                'method': self.__service_name,
                'params': args,
                'id': AuthServiceProxy.__id_count
            }
        )

        parsed_response = await self._parse_response(response)
        if parsed_response.get('error') is not None:
            raise JSONRPCException(parsed_response['error'])
        elif 'result' not in parsed_response:
            raise JSONRPCException({'code': -343, 'message': 'missing JSON-RPC result'})
            
        return parsed_response['result']

    async def batch_(self, rpc_calls):
        """Batch RPC call.
           Pass array of arrays: [ [ "method", params... ], ... ]
           Returns array of results.
        """
        batch_data = []
        for rpc_call in rpc_calls:
            AuthServiceProxy.__id_count += 1
            m = rpc_call.pop(0)
            batch_data.append({"jsonrpc":"2.0", "method":m, "params":rpc_call, "id":AuthServiceProxy.__id_count})

        response = await self._post(batch_data)

        results = []
        responses = await self._parse_response(response)
        if isinstance(responses, (dict,)):
            if ('error' in responses) and (responses['error'] is not None):
                raise JSONRPCException(responses['error'])
            raise JSONRPCException({
                'code': -32700, 'message': 'Parse error'})
        for response in responses:
            if response['error'] is not None:
                raise JSONRPCException(response['error'])
            elif 'result' not in response:
                raise JSONRPCException({
                    'code': -343, 'message': 'missing JSON-RPC result'})
            else:
                results.append(response['result'])
        return results

    async def _post(self, data):
        postdata = json.dumps(data, default=EncodeDecimal)

        log.debug(f"-{AuthServiceProxy.__id_count}-> {self.__service_name} {postdata}")

        response = await self.__conn.post(
            f"http://{self.__url.hostname}:{self.__url.port}",
            auth=aiohttp.BasicAuth(self.__url.username, self.__url.password), 
            data=postdata,
            headers={
                'Host': self.__url.hostname,
                'User-Agent': USER_AGENT,
                'Content-type': 'application/json'
                }
        )
        return response

    async def _parse_response(self, response):
        content_type = response.headers['Content-Type']
        if content_type != 'application/json':
            raise JSONRPCException({
                'code': -342, 'message': 'non-JSON HTTP response with \'%i %s\' from server' % (response.status, response.reason)})

        text = await response.text()
        response_json = json.loads(text, parse_float=decimal.Decimal)
        if "error" in response_json and response_json["error"] is None:
            log.debug(f"<-{response_json['id']}- {response_json}")
        else:
            log.debug(f"<-- {response_json}")
        return response_json
