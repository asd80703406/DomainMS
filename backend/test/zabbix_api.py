#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/22 10:49
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: zabbix_api.py

import json,requests

#url and url header
#zabbix的api 地址，用户名，密码，这里修改为自己实际的参数
zabbix_url="http://zabbix.tigerbrokers.net/api_jsonrpc.php"
zabbix_header = {"Content-Type":"application/json"}
zabbix_user   = "wangzhigang"
zabbix_pass   = "Asd11111111"
auth_code     = ""

#auth user and password
#用户认证信息的部分，最终的目的是得到一个SESSIONID
#这里是生成一个json格式的数据，用户名和密码
def get_zabbix_auth():
    auth_data = json.dumps(
            {
                "jsonrpc":"2.0",
                "method":"user.login",
                "params":
                        {
                            "user":zabbix_user,
                            "password":zabbix_pass
                        },
                "id":0
            })
    # create request object
    request = requests.post(zabbix_url,data=auth_data, headers=zabbix_header)

    auth_code = request.json()['result']
    return auth_code

# auth_code='a7f395e2bc0d265aedb945ae1bc854b4'
def get_host_items():
    auth_code = get_zabbix_auth()
    get_host_ids = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid"],
                # "output": "extend",
                "filter": {
                    "ip": ["124.250.34.6", "124.250.34.7"],
                },
            },
            "auth": auth_code,
            "id": 1,
        })
    request = requests.post(zabbix_url, data=get_host_ids, headers=zabbix_header)

    itemids_json = request.json()['result']
    itemids = []
    [ itemids.append(x["hostid"]) for x in itemids_json ]
    print(itemids)#10608 10609

    get_host_lastvalues = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["key_", "lastvalue", "lastclock"],
                "hostids": itemids,
                "search": {
                    "key_": "nginx"
                },

                # filter: {
                #
                # },
                # "sortfield": "key_"
            },
            "auth": auth_code,
            "id": 2
        })
    request = requests.post(zabbix_url, data=get_host_lastvalues, headers=zabbix_header)

    print(request.json())
# get_host_items()
