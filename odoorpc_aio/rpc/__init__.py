# Copyright 2018 Sebastien Alix <https://usr-src.org>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""This module provides `Connector` classes to communicate with an `Odoo`
server with the `JSON-RPC` protocol or through simple HTTP requests.

Web controllers of `Odoo` expose two kinds of methods: `json` and `http`.
These methods can be accessed from the connectors of this module.
"""
import aiohttp

from odoorpc.rpc import Connector as SynchronousConnector

from . import jsonrpclib


class Connector(SynchronousConnector):
    async def __aenter__(self):
       await self._client_session.__aenter__()

    async def __aexit__(self, exc_type, exc, tb):
       await self._client_session.__aexit__(exc_type, exc, tb)


class ConnectorJSONRPC(Connector):
    """Connector class using the `JSON-RPC` protocol.

    .. doctest::
        :options: +SKIP

        >>> from odoorpc_aio import rpc
        >>> cnt = rpc.ConnectorJSONRPC('localhost', port=8069)

    Or:

    .. doctest::
        :options: +SKIP

        >>> async with rpc.ConnectorJSONRPC('localhost', port=8069) as cnt:
        ...     pass

    .. doctest::
        :hide:

        >>> from odoorpc_aio import rpc
        >>> cnt = rpc.ConnectorJSONRPC(HOST, port=PORT)
        >>> async with rpc.ConnectorJSONRPC(HOST, port=PORT) as cnt:
        ...     pass

    Open a user session:

    .. doctest::
        :options: +SKIP

        >>> await cnt.proxy_json.web.session.authenticate(db='db_name', login='admin', password='password')
        {'id': 51373612,
         'jsonrpc': '2.0',
         'result': {'company_id': 1,
                    'currencies': {'1': {'digits': [69, 2],
                                         'position': 'after',
                                         'symbol': '\u20ac'},
                                   '3': {'digits': [69, 2],
                                         'position': 'before',
                                         'symbol': '$'}},
                    'db': 'db_name',
                    'is_admin': True,
                    'is_superuser': True,
                    'name': 'Administrator',
                    'partner_id': 3,
                    'server_version': '10.0',
                    'server_version_info': [10, 0, 0, 'final', 0, ''],
                    'session_id': '6dd7a34f16c1c67b38bfec413cca4962d5c01d53',
                    'uid': 1,
                    'user_companies': False,
                    'user_context': {'lang': 'en_US',
                                     'tz': 'Europe/Brussels',
                                     'uid': 1},
                    'username': 'admin',
                    'web.base.url': 'http://localhost:8069',
                    'web_tours': []}}

    .. doctest::
        :hide:
        :options: +NORMALIZE_WHITESPACE

        >>> from odoorpc_aio.tools import v
        >>> data = cnt.proxy_json.web.session.authenticate(db=DB, login=USER, password=PWD)
        >>> keys = ['company_id', 'db', 'session_id', 'uid', 'user_context', 'username']
        >>> if v(VERSION) >= v('10.0'):
        ...     keys.extend([
        ...         'currencies', 'is_admin', 'is_superuser', 'name',
        ...         'partner_id', 'server_version', 'server_version_info',
        ...         'user_companies', 'web.base.url', 'web_tours',
        ...     ])
        >>> if v(VERSION) >= v('11.0'):
        ...     keys.extend([
        ...         'is_system',
        ...     ])
        ...     keys.remove('is_admin')
        >>> all([key in data['result'] for key in keys])
        True

    Read data of a partner:

    .. doctest::
        :options: +SKIP

        >>> cnt.proxy_json.web.dataset.call(model='res.partner', method='read', args=[[1]])
        {'jsonrpc': '2.0', 'id': 454236230,
         'result': [{'id': 1, 'comment': False, 'ean13': False, 'property_account_position': False, ...}]}

    .. doctest::
        :hide:

        >>> data = cnt.proxy_json.web.dataset.call(model='res.partner', method='read', args=[[1]])
        >>> 'jsonrpc' in data and 'id' in data and 'result' in data
        True

    You can send requests this way too:

    .. doctest::
        :options: +SKIP

        >>> cnt.proxy_json['/web/dataset/call'](model='res.partner', method='read', args=[[1]])
        {'jsonrpc': '2.0', 'id': 328686288,
         'result': [{'id': 1, 'comment': False, 'ean13': False, 'property_account_position': False, ...}]}

    .. doctest::
        :hide:

        >>> data = cnt.proxy_json['/web/dataset/call'](model='res.partner', method='read', args=[[1]])
        >>> 'jsonrpc' in data and 'id' in data and 'result' in data
        True

    Or like this:

    .. doctest::
        :options: +SKIP

        >>> cnt.proxy_json['web']['dataset']['call'](model='res.partner', method='read', args=[[1]])
        {'jsonrpc': '2.0', 'id': 102320639,
         'result': [{'id': 1, 'comment': False, 'ean13': False, 'property_account_position': False, ...}]}

    .. doctest::
        :hide:

        >>> data = cnt.proxy_json['web']['dataset']['call'](model='res.partner', method='read', args=[[1]])
        >>> 'jsonrpc' in data and 'id' in data and 'result' in data
        True
    """
    def __init__(self, host, port=8069, timeout=120, version=None,
                       deserialize=True, client_session=None):
        super(ConnectorJSONRPC, self).__init__(host, port, timeout, version)
        self.deserialize = deserialize
        if client_session is None:
            client_session = aiohttp.ClientSession()
        self._client_session = client_session
        self._proxy_json, self._proxy_http = self._get_proxies()

    def _get_proxies(self):
        """Returns the :class:`ProxyJSON <odoorpc_aio.rpc.jsonrpclib.ProxyJSON>`
        and :class:`ProxyHTTP <odoorpc_aio.rpc.jsonrpclib.ProxyHTTP>` instances
        corresponding to the server version used.
        """
        proxy_json = jsonrpclib.ProxyJSON(
            self.host, self.port, self._timeout,
            ssl=self.ssl, deserialize=self.deserialize,
            client_session=self._client_session)
        proxy_http = jsonrpclib.ProxyHTTP(
            self.host, self.port, self._timeout,
            ssl=self.ssl, client_session=self._client_session)
        return proxy_json, proxy_http

    async def detect_version(self):
        """Detect and store the server version."""
        # TODO run this during the first async request
        if self.version is None:
            result = await self._proxy_json.web.webclient.version_info()
            if 'server_version' in result['result']:
                self.version = result['result']['server_version']

    @property
    def proxy_json(self):
        """Return the JSON proxy."""
        return self._proxy_json

    @property
    def proxy_http(self):
        """Return the HTTP proxy."""
        return self._proxy_http

    @property
    def timeout(self):
        """Return the timeout."""
        return self._proxy_json._timeout

    @timeout.setter
    def timeout(self, timeout):
        """Set the timeout."""
        self._proxy_json._timeout = timeout
        self._proxy_http._timeout = timeout


class ConnectorJSONRPCSSL(ConnectorJSONRPC):
    """Connector class using the `JSON-RPC` protocol over `SSL`.

    .. doctest::
        :options: +SKIP

        >>> from odoorpc import rpc
        >>> cnt = rpc.ConnectorJSONRPCSSL('localhost', port=8069)

    Or:

    .. doctest::
        :options: +SKIP

        >>> async with rpc.ConnectorJSONRPCSSL('localhost', port=8069) as cnt:
        ...     pass

    .. doctest::
        :hide:

        >>> if 'ssl' in PROTOCOL:
        ...     from odoorpc import rpc
        ...     cnt = rpc.ConnectorJSONRPCSSL(HOST, port=PORT)
        >>>     async with rpc.ConnectorJSONRPCSSL(HOST, port=PORT) as cnt:
        ...         pass
    """

    @property
    def ssl(self):
        return True


PROTOCOLS = {
    'jsonrpc': ConnectorJSONRPC,
    'jsonrpc+ssl': ConnectorJSONRPCSSL,
}
