#!/usr/bin/env python
import asyncio
import os

import odoorpc_aio

HOST = os.environ.get('HOST', 'localhost')
PORT = os.environ.get('PORT', 8069)
DB = os.environ.get('DB', 'odoo')
LOGIN = os.environ.get('LOGIN', 'admin')
PASSWORD = os.environ.get('PASSWORD', 'admin')


async def test_cnt():
    cnt = await odoorpc_aio.rpc.ConnectorJSONRPC(HOST, port=PORT)
    print("SERVER_VERSION = %s" % cnt.version)
    res = await cnt.proxy_json.web.session.authenticate(
        db=DB, login=LOGIN, password=PASSWORD)
    print("AUTH = %s" % res)

loop = asyncio.get_event_loop()
tasks = asyncio.gather(test_cnt())
loop.run_until_complete(tasks)
