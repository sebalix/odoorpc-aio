#!/usr/bin/env python
import asyncio
import os

import aiohttp
import odoorpc_aio

HOST = os.environ.get('HOST', 'localhost')
PORT = os.environ.get('PORT', 8069)
DB = os.environ.get('DB', 'odoo')
LOGIN = os.environ.get('LOGIN', 'admin')
PASSWORD = os.environ.get('PASSWORD', 'admin')


async def test_cnt():
    # client_session = None
    client_session = aiohttp.ClientSession()

    cnt = odoorpc_aio.rpc.ConnectorJSONRPC(
        HOST, port=PORT, client_session=client_session)
    print("CNT", cnt)
    async with cnt:
        print("SERVER_VERSION = %s" % cnt.version)
        await cnt.detect_version()
        print("SERVER_VERSION = %s" % cnt.version)
        res = await cnt.proxy_json.web.session.authenticate(
            db=DB, login=LOGIN, password=PASSWORD)
        print("AUTH = %s" % res)


async def test_odoo():
    # TODO
    pass


loop = asyncio.get_event_loop()
tasks = asyncio.gather(test_cnt())
loop.run_until_complete(tasks)
