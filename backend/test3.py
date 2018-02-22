#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/19 11:35
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: test3.py

from backend.jump_ansible_api import PlayBookRunner
from ansible.inventory.manager import InventoryManager
from backend.jump_ansible_api.inventory import BaseInventory
from ansible.parsing.dataloader import DataLoader
def main():
    host_list= [
        {
        "hostname": "t1",
        "ip": "172.28.49.33",
        "port": "22",
        "username": "lhop",
        "password": None,
        "become": {
            "method": "sudo",
            "user": "root",
            "pass": None,
        },
        "groups": ['世纪互联test'],
        "vars": {},
        },
        {
            "hostname": "",
            "ip": "",
            "port": "",
            "username": "",
            "password": "",
            "private_key": "",
            "become": {
                "method": "sudo",
                "user": "root",
                "pass": None,
            },
            "groups": ['世纪互联test'],
            "vars": {},
        },
    ]
    extra_vars = {"cmd": "-t", "host_list": ['172.28.49.34', '172.28.49.33']}
    inventory = BaseInventory(host_list)
    runner = PlayBookRunner(inventory, playbook_path='backend/playbook_jobs/t2.yml', extra_vars=extra_vars)

    res = runner.run()
    print(res)

def main2():
    from backend.ansible_api2.playbook import MyPlayBookAPI
    extra_vars = {"cmd": "-t", "host_list": ['172.28.49.34', '172.28.49.33']}
    runner = MyPlayBookAPI(playbooks='backend/playbook_jobs/t2.yml', ext_vars=extra_vars)
    res = runner.run()
    # runner.run()
    # res = runner.get_result()
    print('res', res)


if __name__ == '__main__':
    main2()
