#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/27 16:56
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: test2.py
import json
from ansible import constants as C
from collections import namedtuple
from ansible.parsing.dataloader import DataLoader
# from ansible.vars import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.plugins.callback import CallbackBase
# from callback import YunweiCallback
from ansible.utils.ssh_functions import check_for_controlpersist

# 调用自定义Inventory
# from inventory import YunweiInventory as Inventory
try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()
class ResultCallback(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """

    def __init__(self, *args):
        super(ResultCallback, self).__init__(display=None)
        self.status_ok = json.dumps({})
        self.status_fail = json.dumps({})
        self.status_unreachable = json.dumps({})
        self.status_playbook = ''
        self.status_no_hosts = False
        self.host_ok = {}
        self.host_failed = {}
        self.host_unreachable = {}
    #
    def v2_runner_on_ok(self, result):
        host = result._host.get_name()
        self.runner_on_ok(host, result._result)
        # self.status_ok=json.dumps({host:result._result},indent=4)
        if result._result.get("stdout_lines") and host not in self.host_ok:
            self.host_ok[host] = result._result.get("stdout_lines")
        elif result._result.get("stderr") and host not in self.host_ok:
            self.host_ok[host] = result._result.get("stderr")
        elif result._result.get("stdout") and host not in self.host_ok:
            self.host_ok[host] = result._result.get("stdout")
        else:
            self.host_ok[host] = None
            # print(result._result)
        # print(1)
        # print(self.host_ok)
    #
    def v2_runner_on_failed(self, result, ignore_errors=False):
        host = result._host.get_name()
        self.runner_on_failed(host, result._result, ignore_errors)
        self.status_fail=json.dumps({host:result._result},indent=4)
        self.host_failed[host] = result
    #
    # def v2_runner_on_unreachable(self, result):
    #     host = result._host.get_name()
    #     self.runner_on_unreachable(host, result._result)
    #     # self.status_unreachable=json.dumps({host:result._result},indent=4)
    #     self.host_unreachable[host] = result
    #
    # def v2_playbook_on_no_hosts_matched(self):
    #     self.playbook_on_no_hosts_matched()
    #     self.status_no_hosts = True
    #
    # def v2_playbook_on_play_start(self, play):
    #     self.playbook_on_play_start(play.name)
    #     self.playbook_path = play.name
    # def v2_runner_on_ok(self, result, **kwargs):
    #     """Print a json representation of the result
    #
    #     This method could store the result in an instance attribute for retrieval later
    #     """
    #     # self.status_result = json.dumps({})
    #     print(dir(self))
    #     host = result._host
    #     # print(self.runner_on_ok())
    #     # print(json.dumps({host.name: result._result}, indent=4))
    #     if result._result.get("stdout_lines"):
    #         self.status_result = json.dumps({host.name: result._result.get('stdout_lines')}, indent=4)
    #         print(self.status_result)


class YunweiPlaybookExecutor(PlaybookExecutor):

    '''重写PlayBookExecutor'''
    def __init__(self, playbooks, inventory, variable_manager, loader, options, passwords, stdout_callback=None):
        self._playbooks        = playbooks
        self._inventory        = inventory
        self._variable_manager = variable_manager
        self._loader           = loader
        self._options          = options
        self.passwords         = passwords
        self._unreachable_hosts = dict()

        if options.listhosts or options.listtasks or options.listtags or options.syntax:
            self._tqm = None
        else:
            self._tqm = TaskQueueManager(inventory=inventory, variable_manager=variable_manager, loader=loader, options=options, passwords=self.passwords, stdout_callback=stdout_callback)

        # Note: We run this here to cache whether the default ansible ssh
        # executable supports control persist.  Sometime in the future we may
        # need to enhance this to check that ansible_ssh_executable specified
        # in inventory is also cached.  We can't do this caching at the point
        # where it is used (in task_executor) because that is post-fork and
        # therefore would be discarded after every task.
        check_for_controlpersist(C.ANSIBLE_SSH_EXECUTABLE)

class PlayBookJob(object):
    '''封装一个playbook接口,提供给外部使用'''
    def __init__(self,playbooks,ssh_user='lhop',passwords='null',project_name='all',ack_pass=False,forks=5,ext_vars=None):
        self.playbooks = playbooks
        # self.host_list = host_list
        self.ssh_user  = ssh_user
        self.passwords = dict(vault_pass=passwords)
        self.project_name = project_name
        self.ack_pass  = ack_pass
        self.forks     = forks
        self.connection='smart'
        self.ext_vars  = ext_vars

        ## 用来加载解析yaml文件或JSON内容,并且支持vault的解密
        self.loader    = DataLoader()

        # 根据inventory加载对应变量
        self.inventory = InventoryManager(loader=self.loader, sources=['/etc/ansible/hosts'])

        # 管理变量的类，包括主机，组，扩展等变量，之前版本是在 inventory中的
        self.variable_manager = VariableManager(loader=self.loader, inventory=self.inventory)
        self.variable_manager.extra_vars = self.ext_vars
        # print(self.variable_manager.get_vars())
        # print(self.variable_manager.get_vars()) # 所有主机信息

        self.variable_manager.set_inventory(self.inventory)

        # 初始化需要的对象1
        self.Options = namedtuple('Options',
                                 ['connection',
                                 'remote_user',
                                 'ask_sudo_pass',
                                 'verbosity',
                                 'ack_pass',
                                 'module_path',
                                 'forks',
                                 'become',
                                 'become_method',
                                 'become_user',
                                 'check',
                                 'listhosts',
                                 'listtasks',
                                 'listtags',
                                 'syntax',
                                 'sudo_user',
                                 'sudo',
                                  'diff'
                                 ])

        # 初始化需要的对象2
        self.options = self.Options(connection=self.connection,
                                    remote_user=self.ssh_user,
                                    ack_pass=self.ack_pass,
                                    sudo_user=self.ssh_user,
                                    forks=self.forks,
                                    sudo='yes',
                                    ask_sudo_pass=False,
                                    verbosity=5,
                                    module_path=None,
                                    become=True,
                                    become_method='sudo',
                                    become_user='root',
                                    check=None,
                                    listhosts=None,
                                    listtasks=None,
                                    listtags=None,
                                    syntax=None,
                                    diff=False
                                   )

        # 初始化console输出
        self.callback = ResultCallback()


        # 直接开始
        # return self.run()

    def get_result(self):
        # print(dir(self.callback))
        # print("host_ok:", self.callback.host_ok)
        return self.callback.host_ok

    # def get_result(self):
        # self.result_all = {'success': {}, 'fail': {}, 'unreachable': {}}
        # # print result_all
        # # print dir(self.results_callback)
        # for host, result in self.results_callback.host_ok.items():
        #     self.result_all['success'][host] = result._result
        #
        # for host, result in self.results_callback.host_failed.items():
        #     self.result_all['failed'][host] = result._result['msg']
        #
        # for host, result in self.results_callback.host_unreachable.items():
        #     self.result_all['unreachable'][host] = result._result['msg']
        #
        # for i in self.result_all['success'].keys():
        #     print(i, self.result_all['success'][i])
        # self.result_msg = self.callback.v2_runner_item_on_ok()
        # return self.result_msg

        # print(self.result_all['fail'])
        # print(self.result_all['unreachable'])


    def run(self):
        # pb = None
        pb = YunweiPlaybookExecutor(
            playbooks            = self.playbooks,
            inventory            = self.inventory,
            variable_manager     = self.variable_manager,
            loader               = self.loader,
            options              = self.options,
            passwords            = self.passwords,
            stdout_callback      = self.callback
        )

        # pb._tqm._stdout_callback = self.callback

        pb.run()
        del pb

        return self.get_result()

        # return self.callback.status_result



if __name__ == "__main__":
    import subprocess
    # sql = "select ip2 from "
    host_list = ['172.28.48.6', '172.28.48.7']
    pb = PlayBookJob(playbooks=['get_nginx_request_status.yml'],
                # host_list=host_list,
                ssh_user='lhop',
                project_name="test",
                forks=20,)
