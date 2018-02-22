#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/27 17:06
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: inventory.py

import fnmatch

from ansible.compat.six import string_types, iteritems
from ansible import constants as C
from ansible.errors import AnsibleError

# from ansible.inventory.dir import InventoryDirectory, get_file_parser
from ansible.inventory.group import Group
from ansible.inventory.host import Host
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.utils.addresses import parse_address
# from ansible.plugins import vars_loader
from ansible.plugins.loader import vars_loader
from ansible.utils.vars import combine_vars
from ansible.utils.path import unfrackpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

HOSTS_PATTERNS_CACHE = {}
from ansible.inventory import Inventory
class YunweiInventory(Inventory):
    '''重写Inventory'''
    def __init__(self, loader, variable_manager, group_name, ext_vars=None,host_list=C.DEFAULT_HOST_LIST):

        # the host file file, or script path, or list of hosts
        # if a list, inventory data will NOT be loaded
        # self.host_list = unfrackpath(host_list, follow=False)
        # 传入的hosts
        self.host_list  = host_list
        # 传入的项目名也是组名
        self.group_name = group_name
        # 传入的外部变量,格式为字典
        self.ext_vars   = ext_vars
        # caching to avoid repeated calculations, particularly with
        # external inventory scripts.

        self._vars_per_host    = {}
        self._vars_per_group   = {}
        self._hosts_cache      = {}
        self._pattern_cache    = {}
        self._group_dict_cache = {}
        self._vars_plugins     = []

        self._basedir = self.basedir()

        # Contains set of filenames under group_vars directories
        self._group_vars_files = self._find_group_vars_files(self._basedir)
        self._host_vars_files = self._find_host_vars_files(self._basedir)

        # to be set by calling set_playbook_basedir by playbook code
        self._playbook_basedir = None

        # the inventory object holds a list of groups
        self.groups = {}

        # a list of host(names) to contain current inquiries to
        self._restriction = None
        self._subset = None

        # clear the cache here, which is only useful if more than
        # one Inventory objects are created when using the API directly
        self.clear_pattern_cache()
        self.clear_group_dict_cache()

        self.parse_inventory(host_list)

    def parse_inventory(self, host_list):

        if isinstance(host_list, string_types):
            if "," in host_list:
                host_list = host_list.split(",")
                host_list = [ h for h in host_list if h and h.strip() ]

        self.parser = None

        # Always create the 'all' and 'ungrouped' groups, even if host_list is
        # empty: in this case we will subsequently an the implicit 'localhost' to it.

        ungrouped = Group('ungrouped')
        all = Group('all')
        all.add_child_group(ungrouped)

        # 加一个本地IP
        local_group = Group('local')

        # 自定义组名
        zdy_group_name = Group(self.group_name)
        self.groups = {self.group_name:zdy_group_name,"all":all,"ungrouped":ungrouped,"local":local_group}
        #self.groups = dict(all=all, ungrouped=ungrouped)

        if host_list is None:
            pass
        elif isinstance(host_list, list):
            # 默认添加一个本地IP
            (lhost, lport) = parse_address('127.0.0.1', allow_ranges=False)
            new_host = Host(lhost, lport)
            local_group.add_host(new_host)

            for h in host_list:
                try:
                    (host, port) = parse_address(h, allow_ranges=False)
                except AnsibleError as e:
                    display.vvv("Unable to parse address from hostname, leaving unchanged: %s" % to_text(e))
                    host = h
                    port = None

                new_host = Host(host, port)
                if h in C.LOCALHOST:
                    # set default localhost from inventory to avoid creating an implicit one. Last localhost defined 'wins'.
                    if self.localhost is not None:
                        display.warning("A duplicate localhost-like entry was found (%s). First found localhost was %s" % (h, self.localhost.name))
                    display.vvvv("Set default localhost to %s" % h)
                    self.localhost = new_host
                # 为组添加host
                zdy_group_name.add_host(new_host)
                # 为主机组添加额外参数
                # 添加外部变量
                if self.ext_vars and isinstance(self.ext_vars,dict):
                    for k,v in self.ext_vars.items():
                        zdy_group_name.set_variable(k,v)
                        local_group.set_variable(k,v)

        elif self._loader.path_exists(host_list):
            # TODO: switch this to a plugin loader and a 'condition' per plugin on which it should be tried, restoring 'inventory pllugins'
            if self.is_directory(host_list):
                # Ensure basedir is inside the directory
                host_list = os.path.join(self.host_list, "")
                self.parser = InventoryDirectory(loader=self._loader, groups=self.groups, filename=host_list)
            else:
                self.parser = get_file_parser(host_list, self.groups, self._loader)
                vars_loader.add_directory(self._basedir, with_subdir=True)

            if not self.parser:
                # should never happen, but JIC
                raise AnsibleError("Unable to parse %s as an inventory source" % host_list)
        else:
            display.warning("Host file not found: %s" % to_text(host_list))

        self._vars_plugins = [ x for x in vars_loader.all(self) ]

        # set group vars from group_vars/ files and vars plugins
        for g in self.groups:
            group = self.groups[g]
            group.vars = combine_vars(group.vars, self.get_group_variables(group.name))
            self.get_group_vars(group)

        # get host vars from host_vars/ files and vars plugins
        for host in self.get_hosts(ignore_limits=True, ignore_restrictions=True):
            host.vars = combine_vars(host.vars, self.get_host_variables(host.name))
            self.get_host_vars(host)