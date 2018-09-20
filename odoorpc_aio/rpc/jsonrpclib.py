# Copyright 2018 Sebastien Alix <https://usr-src.org>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Provides the :class:`ProxyJSON` class for JSON-RPC requests."""
import json
import random
import io

import aiohttp

from odoorpc.rpc.jsonrpclib import URLBuilder


def encode_data(data):
    try:
        return bytes(data, 'utf-8')
    except:
        return bytes(data)


def decode_data(data):
    return io.StringIO(data.decode('utf-8'))


class Proxy(object):
    """Base class to implement a proxy to perform requests."""
    def __init__(self, host, port, timeout=120, ssl=False,
                 client_session=None):
        self._root_url = "{http}{host}:{port}".format(
            http=(ssl and "https://" or "http://"), host=host, port=port)
        self._timeout = timeout
        self._builder = URLBuilder(self)
        if client_session is None:
            client_session = aiohttp.ClientSession()
        self._client_session = client_session

    def __getattr__(self, name):
        return getattr(self._builder, name)

    def __getitem__(self, url):
        return self._builder[url]


class ProxyJSON(Proxy):
    """The :class:`ProxyJSON` class provides a dynamic access
    to all JSON methods.
    """
    def __init__(self, host, port, timeout=120, ssl=False, deserialize=True,
                 client_session=None):
        Proxy.__init__(self, host, port, timeout, ssl, client_session)
        self._deserialize = deserialize

    async def __call__(self, url, params):
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": random.randint(0, 1000000000),
        })
        if url.startswith('/'):
            url = url[1:]
        full_url = '/'.join([self._root_url, url])
        headers = {'Content-Type': 'application/json'}
        response = await self._client_session.post(
            full_url, data=encode_data(data), headers=headers)
        resp_data = await response.read()
        if not self._deserialize:
            return resp_data
        return json.load(decode_data(resp_data))


class ProxyHTTP(Proxy):
    """The :class:`ProxyHTTP` class provides a dynamic access
    to all HTTP methods.
    """
    async def __call__(self, url, data=None, headers=None):
        full_url = '/'.join([self._root_url, url]),
        encoded_data = encode_data(data) if data else None
        return await self._client_session.post(
            full_url, data=encoded_data,
            headers=headers, timeout=self._timeout)
