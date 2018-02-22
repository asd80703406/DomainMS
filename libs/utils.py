#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/20 17:04
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: utils.py


import json
from datetime import date, datetime
from handle.base import BaseResponse

class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        # elif isinstance(obj, BaseResponse):
        #     print(BaseResponse["data"])
        #     return {"data" : BaseResponse["data"]}
        else:
            return json.JSONEncoder.default(self, obj)