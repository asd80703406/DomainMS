#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 10:47
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: database.py

import torndb
import config

def db():
    return torndb.Connection(config.DB_HOST, config.DB_NAME, config.DB_USER, config.DB_PASSWORD, max_idle_time=300, time_zone="+8:00")


