#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/27 19:57
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: test3.py

import json,os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.errors import AnsibleParserError
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase

class mycallback(CallbackBase):
    #这里是状态回调，各种成功失败的状态,里面的各种方法其实都是从写于CallbackBase父类里面的，其实还有很多，可以根据需要拿出来用
    def __init__(self,*args):
        super(mycallback,self).__init__(display=None)
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

class my_ansible_play():
    #这里是ansible运行
    #初始化各项参数，大部分都定义好，只有几个参数是必须要传入的
    def __init__(self, playbooks, ssh_user='lhop', passwords='null', project_name='all', ack_pass=False,
                 forks=5, ext_vars=None):
        self.playbooks = playbooks
        # self.host_list = host_list
        self.ssh_user = ssh_user
        self.passwords = dict(vault_pass=passwords)
        self.project_name = project_name
        self.ack_pass = ack_pass
        self.forks = forks
        self.connection = 'smart'
        self.ext_vars = ext_vars
        self.playbook_path = self.playbooks

        ## 用来加载解析yaml文件或JSON内容,并且支持vault的解密
        self.loader = DataLoader()

        # 根据inventory加载对应变量
        self.inventory = InventoryManager(loader=self.loader, sources=['/etc/ansible/hosts'])

        # 管理变量的类，包括主机，组，扩展等变量，之前版本是在 inventory中的
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        # self.variable_manager.extra_vars = {"host_list": self.host_list}
        self.variable_manager.extra_vars = self.ext_vars

        # print(self.variable_manager.get_vars()) # 所有主机信息

        self.variable_manager.set_inventory(self.inventory)

        # 初始化需要的对象1
        Options = namedtuple('Options',
                             ['listtags', 'listtasks', 'listhosts', 'syntax', 'connection', 'module_path',
                              'forks', 'private_key_file', 'ssh_common_args', 'ssh_extra_args', 'sftp_extra_args',
                              'scp_extra_args', 'become', 'become_method', 'become_user', 'verbosity', 'check', 'diff'])

        self.options = Options(listtags=False, listtasks=False,
                               listhosts=False, syntax=False,
                               connection='ssh', module_path=None,
                               forks=10, private_key_file=None,
                               ssh_common_args=None, ssh_extra_args=None,
                               sftp_extra_args=None, scp_extra_args=None,
                               become=None, become_method=None,
                               become_user=None,
                               verbosity=None, check=False, diff=False)
            # 初始化需要的对象2



    #定义运行的方法和返回值
    def run(self):
        complex_msg={}
        if not os.path.exists(self.playbook_path):
            code = 50000
            results={'playbook':self.playbook_path,'msg':self.playbook_path+' playbook is not exist','flag':False}

        pbex= PlaybookExecutor(playbooks=[self.playbook_path],
                       inventory=self.inventory,
                       variable_manager=self.variable_manager,
                       loader=self.loader,
                       options=self.options,
                       passwords=self.passwords)
        self.results_callback=mycallback()
        pbex._tqm._stdout_callback=self.results_callback
        try:
            code=pbex.run()
        except AnsibleParserError:
            code = 50000
            results={'playbook':self.playbook_path,'msg':self.playbook_path+' playbook have syntax error','flag':False}

            return code,results
        if self.results_callback.status_no_hosts:
            code = 5000
            results={'playbook':self.playbook_path,'msg':self.results_callback.status_no_hosts,'flag':False,'executed':False}

            return code,results

    def get_result(self):
        self.result_all={'success':{},'failed':{},'unreachable':{}}

        for host, result in self.results_callback.host_ok.items():
            self.result_all['success'][host] = result._result

        for host, result in self.results_callback.host_failed.items():
            self.result_all['failed'][host] = result._result['msg']

        for host, result in self.results_callback.host_unreachable.items():
            self.result_all['unreachable'][host]= result._result['msg']

        # for i in self.result_all['success'].keys():
        #     print('Success Info', i,self.result_all['success'][i])
        # print('Failed Info', self.result_all['failed'])
        # print('Unreachable Info', self.result_all['unreachable'])
        return self.result_all



if __name__ =='__main__':
    host_list = ['172.28.49.33', '172.28.49.34']
    ext_vars = {"host_list": host_list, 'cmd': '-t'}
    # play_book = my_ansible_play(playbooks='./get_nginx_request_status.yml',
    play_book = my_ansible_play(playbooks='./execute_nginx_cmd.yml',
                     ssh_user='lhop',
                     project_name="test",
                     forks=20, ext_vars=ext_vars)
    play_book.run()
    play_book.get_result()