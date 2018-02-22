#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/2 20:06
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: test.py

import json
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible.executor.playbook_executor import PlaybookExecutor
from backend.ansible_api.callback import MyCallBack

# ResultCallback = MyCallBack

class myplaybook(object):
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

        # initialize needed objects
        self.loader = DataLoader()
        # passwords = dict(vault_pass='secret')

        # Instantiate our ResultCallback for handling results as they come in
        self.results_callback = MyCallBack()
        self.inventory = InventoryManager(loader=self.loader, sources=['/etc/ansible/hosts'])
        # 管理变量的类，包括主机，组，扩展等变量，之前版本是在 inventory中的
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        # self.variable_manager.extra_vars = {"host_list": self.host_list}
        self.variable_manager.extra_vars = self.ext_vars

    def run(self):
        # create play with tasks
        # play_source =  dict(
        #         name = "Ansible Play",
        #         hosts = 'localhost',
        #         gather_facts = 'no',
        #         tasks = [
        #             dict(action=dict(module='shell', args='ls'), register='shell_out'),
        #             dict(action=dict(module='debug', args=dict(msg='{{shell_out.stdout}}')))
        #          ]
        #     )
        from ansible.playbook import Playbook
        pb = Playbook.load(self.playbook_path, variable_manager=self.variable_manager, loader=self.loader)
        # pbex = PlaybookExecutor(playbooks=[self.playbook_path],
        #                         inventory=self.inventory,
        #                         variable_manager=self.variable_manager,
        #                         loader=self.loader,
        #                         options=self.options,
        #                         passwords=self.passwords)
        # play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)
        plays = pb.get_plays()
        print("plays_type", type(plays))
        for play in plays:
            print("play type:", type(play))
            print("play :", dir(play))
            # actually run it
            tqm = None
            try:
                tqm = TaskQueueManager(
                          inventory=self.inventory,
                          variable_manager=self.variable_manager,
                          loader=self.loader,
                          options=self.options,
                          passwords=self.passwords,
                          stdout_callback=self.results_callback,  # Use our custom callback instead of the ``default`` callback plugin
                      )
                result = tqm.run(play)
            finally:
                if tqm is not None:
                    tqm.cleanup()

    def get_result(self):
        self.result_all = {'success': {}, 'failed': {}, 'unreachable': {}}

        for host, result in self.results_callback.host_ok.items():
            self.result_all['success'][host] = result._result

        for host, result in self.results_callback.host_failed.items():
            self.result_all['failed'][host] = result._result['msg']

        for host, result in self.results_callback.host_unreachable.items():
            self.result_all['unreachable'][host] = result._result['msg']

        # for i in self.result_all['success'].keys():
        #     print('Success Info', i,self.result_all['success'][i])
        # print('Failed Info', self.result_all['failed'])
        # print('Unreachable Info', self.result_all['unreachable'])
        return self.result_all
