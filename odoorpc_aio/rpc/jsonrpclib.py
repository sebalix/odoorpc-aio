# Copyright 2018 Sebastien Alix <https://usr-src.org>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Provides the :class:`ProxyJSON` class for JSON-RPC requests."""
import json
import logging
import random
import io

import aiohttp

from odoorpc.rpc.jsonrpclib import (
    encode_data, get_json_log_data, URLBuilder,
    LOG_HIDDEN_JSON_PARAMS,
    LOG_JSON_SEND_MSG, LOG_JSON_RECV_MSG,
    LOG_HTTP_SEND_MSG, LOG_HTTP_RECV_MSG)

logger = logging.getLogger(__name__)


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

    def _get_full_url(self, url):
        return '/'.join([self._root_url, url])


class ProxyJSON(Proxy):
    """The :class:`ProxyJSON` class provides a dynamic access
    to all JSON methods.
    """
    def __init__(self, host, port, timeout=120, ssl=False, deserialize=True,
                 client_session=None):
        Proxy.__init__(self, host, port, timeout, ssl, client_session)
        self._deserialize = deserialize

    async def __call__(self, url, params=None):
        if params is None:
            params = {}
        data = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": params,
            "id": random.randint(0, 1000000000),
        }
        if url.startswith('/'):
            url = url[1:]
        full_url = self._get_full_url(url)
        log_data = get_json_log_data(data)
        logger.debug(
            LOG_JSON_SEND_MSG,
            {'url': full_url, 'data': log_data})
        data_json = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        response = await self._client_session.post(
            full_url, data=encode_data(data_json), headers=headers)
        resp_data = await response.read()
        if not self._deserialize:
            return resp_data
        result = json.load(decode_data(resp_data))
        logger.debug(
            LOG_JSON_RECV_MSG,
            {'url': full_url, 'data': log_data, 'result': result})
        return result


class ProxyHTTP(Proxy):
    """The :class:`ProxyHTTP` class provides a dynamic access
    to all HTTP methods.
    """
    async def __call__(self, url, data=None, headers=None):
        if url.startswith('/'):
            url = url[1:]
        full_url = self._get_full_url(url)
        logger.debug(
            LOG_HTTP_SEND_MSG,
            {'url': full_url, 'data': data and u" (%s)" % data or u""})
        encoded_data = encode_data(data) if data else None
        response = await self._client_session.post(
            full_url, data=encoded_data,
            headers=headers, timeout=self._timeout)
        logger.debug(
            LOG_HTTP_RECV_MSG,
            {'url': full_url,
             'data': data and u" (%s)" % data or u"",
             'result': response})
        return response
