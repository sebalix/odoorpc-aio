# Copyright 2018 Sebastien Alix <https://usr-src.org>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Provides the :class:`ProxyJSON` class for JSON-RPC requests."""
import json
import random
import io

import aiohttp


def encode_data(data):
    try:
        return bytes(data, 'utf-8')
    except:
        return bytes(data)


def decode_data(data):
    return io.StringIO(data.decode('utf-8'))


async def ProxyJSON(host, port, timeout=120, ssl=False,
                    deserialize=True, client_session=None):
    proxy = ProxyJSONAIO(host, port, timeout, ssl, deserialize)
    await proxy._init(client_session)
    return proxy


async def ProxyHTTP(host, port, timeout=120, ssl=False, client_session=None):
    proxy = ProxyHTTPAIO(host, port, timeout, ssl)
    await proxy._init(client_session)
    return proxy


class Proxy(object):
    """Base class to implement a proxy to perform requests."""
    def __init__(self, host, port, timeout=120, ssl=False):
        self._root_url = "{http}{host}:{port}".format(
            http=(ssl and "https://" or "http://"), host=host, port=port)
        self._timeout = timeout
        self._builder = URLBuilder(self)

    async def _init(self, client_session):
        if client_session is None:
            client_session = aiohttp.ClientSession()
        self._client_session = client_session

    def __getattr__(self, name):
        return getattr(self._builder, name)

    def __getitem__(self, url):
        return self._builder[url]


class ProxyJSONAIO(Proxy):
    """The :class:`ProxyJSONAIO` class provides a dynamic access
    to all JSON methods.
    """
    def __init__(self, host, port, timeout=120, ssl=False, deserialize=True):
        Proxy.__init__(self, host, port, timeout, ssl)
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


class ProxyHTTPAIO(Proxy):
    """The :class:`ProxyHTTPAIO` class provides a dynamic access
    to all HTTP methods.
    """
    async def __call__(self, url, data=None, headers=None):
        full_url = '/'.join([self._root_url, url]),
        encoded_data = encode_data(data) if data else None
        return await self._client_session.post(
            full_url, data=encoded_data,
            headers=headers, timeout=self._timeout)


class URLBuilder(object):
    """Auto-builds an URL while getting its attributes.
    Used by the :class:`ProxyJSONAIO` and :class:`ProxyHTTPAIO` classes.
    """
    def __init__(self, rpc, url=None):
        self._rpc = rpc
        self._url = url

    def __getattr__(self, path):
        new_url = self._url and '/'.join([self._url, path]) or path
        return URLBuilder(self._rpc, new_url)

    def __getitem__(self, path):
        if path and path[0] == '/':
            path = path[1:]
        if path and path[-1] == '/':
            path = path[:-1]
        return getattr(self, path)

    def __call__(self, **kwargs):
        return self._rpc(self._url, kwargs)

    def __str__(self):
        return self._url
