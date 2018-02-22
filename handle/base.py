#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 11:41
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: base.py


from tornado.web import RequestHandler
from libs.account import generate_auth_token, Passwd, verify_auth_token

import json


class BaseResponse(object):
    def __init__(self):
        self.code = None
        self.msg = None
        self.data = []

class BaseHandle(RequestHandler):
    def initialize(self):
        if self.request.body: self.request_body_data = json.loads(self.request.body.decode("utf8"))

    def prepare(self):
        if self.request.method == "OPTIONS":
            return self.options()
        TOKEN_FLAG = True # 定义token默认有效
        self.response = BaseResponse()
        token = self.request.headers.get("X-Token")
        if token: # 如果请求header中有token
            username = verify_auth_token(token)
            # print('token/: ', type(token),token)
            # print('username:', username)

            if not username: # 如果无法反解出用户名，则token无效
                TOKEN_FLAG = False
            else:
                self.current_user = username
        else: # 请求header中无token
            TOKEN_FLAG = False
        if not TOKEN_FLAG:
            self.response.code = 50000
            self.response.msg = "请求参数异常"
            self.finish(json.dumps(self.response.__dict__))

    def options(self, *args, **kwargs):
        self.set_status(204)


    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Credentials', 'true')
        self.set_header('Access-Control-Allow-Headers', 'content-type, x-token')
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.set_header('Content-Type', 'application/json; charset=utf-8')
        self.set_header('Access-Control-Allow-Origin', '*')

    @property
    def _db(self):
        return self.application.db

    def on_finish(self):
        self._db.close()


