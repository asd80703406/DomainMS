#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/27 19:57
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: callback.py


from ansible.plugins.callback import CallbackBase
import json

class MyCallBack(CallbackBase):
    #这里是状态回调，各种成功失败的状态,里面的各种方法其实都是从写于CallbackBase父类里面的，其实还有很多，可以根据需要拿出来用
    def __init__(self,*args):
        super(MyCallBack,self).__init__(display=None)
        self.status_ok=json.dumps({})
        self.status_fail=json.dumps({})
        self.status_unreachable=json.dumps({})
        self.status_playbook=''
        self.status_no_hosts=False
        self.host_ok = {}
        self.host_failed={}
        self.host_unreachable={}

    def v2_runner_on_ok(self,result):
        print('Job Run OK')
        host = result._host
        # print(json.dumps({host.name: result._result}, indent=4))
        host=result._host.get_name()
        self.runner_on_ok(host, result._result)
        self.host_ok[host] = result

    def v2_runner_on_failed(self, result, ignore_errors=False):
        print('Run Failed Job')
        host = result._host.get_name()
        # print("failed detail;", result._result)
        self.runner_on_failed(host, result._result, ignore_errors)
        #self.status_fail=json.dumps({host:result._result},indent=4)
        self.host_failed[host] = result

    def v2_runner_on_unreachable(self, result):
        print('Rub unreachable Job')
        host = result._host.get_name()
        self.runner_on_unreachable(host, result._result)
        #self.status_unreachable=json.dumps({host:result._result},indent=4)
        self.host_unreachable[host] = result

    def v2_playbook_on_no_hosts_matched(self):
        print('No hosts matched')
        self.playbook_on_no_hosts_matched()
        self.status_no_hosts=True

    def v2_playbook_on_play_start(self, play):
        print('PlayBook Job Start')
        self.playbook_on_play_start(play.name)
        self.playbook_path=play.name