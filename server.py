#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 10:21
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: server.py

import logging
import os
from tornado import log,httpclient,httpserver,autoreload,ioloop,web
from tornado.options import define, options
import tornado
import config
from handle.sslcert import *
from handle.account import *
from handle.nginxserver import *
from handle.domain import *
from libs import database

class Application(tornado.web.Application):
    def ping_db(self):
        self.db.query("show variables")

    def __init__(self):
        tornado.web.Application.__init__(self, router.Route.get_routes(), **config.settings)
        self.db = database.db()

        # 调用方法 self.application.db


class LogFormatter(tornado.log.LogFormatter):
    def __init__(self):
        super(LogFormatter, self).__init__(
            fmt='%(color)s[%(levelname)s %(asctime)s %(filename)s:%(lineno)d]%(end_color)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def signal_handler(signum, frame):
    # print('Received signal: ', signum)
    os.wait()

if __name__ == '__main__':
    define("port", default=config.APP_PORT, type=int)
    tornado.options.parse_command_line()
    tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient", max_clients=4000)

    [i.setFormatter(LogFormatter()) for i in logging.getLogger().handlers]

    server = tornado.httpserver.HTTPServer(Application(), xheaders=True)
    server.listen(options.port)

    instance = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(instance)

    import signal
    signal.signal(signal.SIGCHLD, signal_handler)
    instance.start()

    logging.info("Exit...")