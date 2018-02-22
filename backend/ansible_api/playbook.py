#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/27 19:57
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: test3.py

import os
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.errors import AnsibleParserError
from ansible.executor.playbook_executor import PlaybookExecutor
from backend.ansible_api.callback import MyCallBack



class MyPlayBookAPI():
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

    #定义运行的方法和返回值
    def run(self):
        # complex_msg={}
        if not os.path.exists(self.playbook_path):
            code=1000
            results={'playbook':self.playbook_path,'msg':self.playbook_path+' playbook is not exist','flag':False}

        pbex = PlaybookExecutor(playbooks=[self.playbook_path],
                       inventory=self.inventory,
                       variable_manager=self.variable_manager,
                       loader=self.loader,
                       options=self.options,
                       passwords=self.passwords)
        self.results_callback=MyCallBack()
        pbex._tqm._stdout_callback=self.results_callback
        try:
            code=pbex.run()
            pbex._tqm.cleanup()

        except AnsibleParserError:
            code=1001
            results={'playbook':self.playbook_path,'msg':self.playbook_path+' playbook have syntax error','flag':False}

            return code,results
        if self.results_callback.status_no_hosts:
            code=1002
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
    # play_book = MyPlayBookAPI(playbooks='./get_nginx_request_status.yml',
    play_book = MyPlayBookAPI(playbooks='/data0/webservice/DomainMS/backend/playbook_jobs/execute_nginx_cmd.yml',
                     ssh_user='lhop',
                     project_name="test",
                     forks=20, ext_vars=ext_vars)
    play_book.run()
    result = play_book.get_result()
    print(result)