#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 10:21
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: config.py
import os
settings = {
    "debug": False,
    "template_path": "templates",
    "static_path": "statics",
    "cookie_secret": "YXRvbS50cmFkZSBpcyB0aGUgYmVzdAo=",
    "login_url": "/login",
}

APP_PORT = 4000

DB_NAME = "nginx"
DB_HOST = ""
DB_USER = "nginx"
DB_PASSWORD = ""

LDAP_CONFIG = {
    "SECRET_KEY" : "",
    "EXPIRATION" : 60*60*24,
    "LDAP" : "",
    "password" : ""
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ssl_save_path = os.path.join(BASE_DIR, "upload/cert")
ssl_remote_save_path = ""
nginx_vhost_path = ""
nginx_configtest_ok_flag = "nginx: the configuration file /usr/local/nginx/conf/nginx.conf syntax is ok\nnginx: configuration file /usr/local/nginx/conf/nginx.conf test is successful"
keepalive_restart_ok_flag = "Stopping keepalived: [  OK  ]\r\nStarting keepalived: [  OK  ]"

LOGIN_TOKEN = ''
API_DOMAIN = 'https://dnsapi.cn/'
Domain_Create_API_URL = "https://dnsapi.cn/Record.Create"

new_dict = {
    "世纪互联": "('世纪互联', '广州机房', '深圳机房')",
    "广州机房": "('世纪互联', '广州机房', '深圳机房')",
    "深圳机房": "('世纪互联', '广州机房', '深圳机房')",
    "将军澳机房": "('将军澳机房', '荃湾机房')",
    "荃湾机房": "('将军澳机房', '荃湾机房')",
}

tiger_domain_list = [ ]
tiger_nginxupstream_function_list = ['rr', 'ip_hash', 'least_conn']
# domain_res = requests.post(Domain_Create_API_URL, json.dumps({
#     'login_token': LOGIN_TOKEN,
#     'domain': ".".join(domain_name.split(".")[-2:]),
#     'sub_domain': domain_name,
#     'record_type': "A",
#     'record_line': region,
#     'value': vip,
# })).json()
# if domain_res["status"]["code"] == 1:
#     self.response.code = 20000
#     self.response.msg = "域名添加成功，入库失败"
