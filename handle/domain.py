#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 11:22
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: domain.py

import router
import json
import traceback
import os
from libs.utils import CJsonEncoder
from handle.base import BaseHandle
from backend.ansible_api.playbook import MyPlayBookAPI
from backend.ansible_api2.playbook import MyPlayBookAPI as NewPlayBookAPI
from config import nginx_vhost_path, tiger_domain_list, tiger_nginxupstream_function_list


def db_record(obj, domain_name, region, domain_type, line1,line2,line3, nginx_upstream_strategy,weight,max_fails,fail_timeout, upstreams_list):
    try:
        if line1 and line2 and line3:
            sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`line2`,`line3`,`last_editor`) " \
                   "VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,line2,line3, obj.current_user)
        elif line1 and line2:
            sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`line2`,`last_editor`) " \
                   "VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,line2, obj.current_user)
        elif line1:
            sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`last_editor`) " \
                   "VALUES ('%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,obj.current_user)
        else: pass
        domain_id = obj._db.execute_lastrowid(sql)
        # sql2 = "select domain_id from domains and domain_type='%s' and domain_name='%s';" % (domain_type, domain_name)
        # res = obj._db.get(sql2)
        # domain_id = res["domain_id"]
        for item in upstreams_list:
            sql3 = "insert into upstream_server (`domain_id`,`lhzq_sn`,`idc`,`ip1`,`ip2`,`function`,`weight`,`max_fails`,`fail_timeout`,`last_editor`) VALUES " \
                   "(%s, '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s' )" % (domain_id, item["lhzq_sn"],item["isp"],item["ip1"],item["ip2"],
                                                                         nginx_upstream_strategy,weight,max_fails,fail_timeout,obj.current_user)
            obj._db.insert(sql3)
        print("数据插入成功")
        return True
    except:
        traceback.print_exc()
        print('%s: %s 记录入库错误，请手动修正'% (domain_type, domain_name))
        return False

def db_update(obj, domain_name, region, domain_type, line1,line2,line3, nginx_upstream_strategy,weight,max_fails,fail_timeout, upstreams_list):
    if line1 and line2 and line3:
        sql = "update domains set region='%s', line1='%s', line2='%s', line3='%s', last_editor='%s' where domain_name='%s' AND " \
              "domain_type='%s'" % (region, line1, line2,line3,obj.current_user, domain_name, domain_type)
        # sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`line2`,`line3`,`last_editor`) " \
        #        "VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,line2,line3, obj.current_user)
    elif line1 and line2:
        sql = "update domains set region='%s', line1='%s', line2='%s',line3=null, last_editor='%s' where domain_name='%s' AND " \
             "domain_type='%s'" % (region, line1, line2, obj.current_user, domain_name, domain_type)
        # sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`line2`,`last_editor`) " \
        #        "VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,line2, obj.current_user)
    elif line1:
        sql = "update domains set region='%s', line1='%s',line2=null,line3=null, last_editor='%s' where domain_name='%s' AND " \
              "domain_type='%s'" % (region, line1, obj.current_user, domain_name, domain_type)
        # sql = "insert into domains (`domain_name`,`region`,`domain_type`,`line1`,`last_editor`) " \
        #        "VALUES ('%s', '%s', '%s', '%s', '%s')" % (domain_name, region, domain_type, line1,obj.current_user)
    else:
        pass
    try:
        print("更新sql:", sql)
        obj._db.execute_lastrowid(sql)
        print("更新sql执行成功")
        domain_id = obj._db.get("select domain_id from domains where domain_name='%s' and domain_type='%s'" % (domain_name, domain_type))["domain_id"]
        print("要删除的doamin_Id为： %s" % domain_id)
    except:
        traceback.print_exc()
        return False
    # sql2 = "select domain_id from domains and domain_type='%s' and domain_name='%s';" % (domain_type, domain_name)
    # res = obj._db.get(sql2)
    # domain_id = res["domain_id"]
    try:
        del_sql = "delete from upstream_server where domain_id='%s'" % domain_id
        print("del_sql: ", del_sql)
        obj._db.execute(del_sql)
        print("删除sql执行成功", del_sql)
    except Exception as e:
        print(e)
        traceback.print_exc()
        print("旧upstream条目删除失败，domain_id：%s" % domain_id)
        return False
    try:
        for item in upstreams_list:
            sql3 = "insert into upstream_server (`domain_id`,`lhzq_sn`,`idc`,`ip1`,`ip2`,`function`,`weight`,`max_fails`,`fail_timeout`,`last_editor`) VALUES " \
                   "(%s, '%s', '%s', '%s','%s', '%s', '%s', '%s', '%s', '%s' )" % (domain_id, item["lhzq_sn"],item["isp"],item["ip1"],item["ip2"],
                                                                         nginx_upstream_strategy,weight,max_fails,fail_timeout,obj.current_user)
            obj._db.insert(sql3)
        print("数据全部更新成功")
        return True
    except:
        traceback.print_exc()
        print('%s: %s 记录入库错误，请手动修正'% (domain_type, domain_name))
        return False

def db_multi_update(obj, domain_list, line1,line2,line3, region):
    for domain_name in domain_list:
        if line1 and line2 and line3:
            sql = "update domains set line1='%s', line2='%s', line3='%s', last_editor='%s' where domain_name='%s' AND " \
                  "region='%s'" % (line1, line2, line3, obj.current_user, domain_name, region)
        elif line1 and line2:
            sql = "update domains set line1='%s', line2='%s',line3=null, last_editor='%s' where domain_name='%s' AND " \
                 "region='%s'" % (line1, line2, obj.current_user, domain_name, region)
        elif line1:
            sql = "update domains set line1='%s', line2=null,line3=null, last_editor='%s' where domain_name='%s' AND " \
                  "region='%s'" % (line1, obj.current_user, domain_name, region)
        else:
            pass
        try:
            print("更新sql:", sql)
            obj._db.execute(sql)
            print("更新sql执行成功: ", domain_name)
        except:
            traceback.print_exc()
            return False
    return True

def db_delete(obj, domain_id):
    sql1 = "delete from domains where domain_id='%s'" % domain_id
    sql2 = "delete from upstream_server where domain_id='%s'" % domain_id
    print(sql1, sql2)
    try:
        obj._db.execute(sql1)
        obj._db.execute(sql2)
        print("域名删除成功")
        return True
    except:
        traceback.print_exc()
        return False


@router.Route("/domain/getAll")
class DomainGetAll(BaseHandle):
    def get(self, *args, **kwargs):
        page = self.get_argument("page")
        page_size = self.get_argument("pagesize")
        page_start = (int(page) - 1) * int(page_size)
        limitsize = int(page_size)
        # sql2 = "select domain_id, domain_name, region, domain_type, line1, line2, line3 from domains limit %d, %d;"
        sql2 = "select a.domain_id, a.domain_name, a.region, a.domain_type, a.line1, a.line2, a.line3, b.lhzq_sn, b.function,b.weight, b.max_fails, b.fail_timeout from domains as a join upstream_server as b on a.domain_id=b.domain_id limit %d, %d;"
        # sql1 = "select id, line from `lines`;"
        # result = self._db.query(sql1)
        # line_dict = {}
        # for item in result:
        #     line_dict[item["id"]] = item["line"]
        # print(line_dict)
        try:
            # new_dict = {}
            result = self._db.query(sql2 % (page_start, limitsize))
            flag = False
            temp_list = []
            index_start = 0
            temp_dict = {}
            for item in result:
                # temp_dict = {}
                if item["domain_id"] in temp_list: # 说明是同一个域名

                    self.response.data[temp_dict["domain_id"]]["upstreams"].append(item["lhzq_sn"])
                    # self.response.data[temp_dict["domain_id"]]["upstreams"] = ",".join(temp_dict["domain_id"]["upstreams"])

                else: # 之前没有处理过，是新域名
                    temp_list.append(item["domain_id"])
                    item["upstreams"] = []
                    item["upstreams"].append(item["lhzq_sn"])
                    temp_dict["domain_id"] = index_start
                    index_start += 1
                    self.response.data.append(item)
            for item in self.response.data:
                item["upstreams"] = ",".join(item["upstreams"])
            #     item["line1"] = line_dict.get(item["line1"], None)
            #     item["line2"] = line_dict.get(item["line2"], None)
            #     item["line3"] = line_dict.get(item["line3"], None)

            self.response.code = 20000
            # self.response.data = result
            self.response.msg = "查询成功"
            self.response.total = len(self.response.data)
        except Exception as e:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(json.dumps(self.response.__dict__, cls=CJsonEncoder))

@router.Route("/domain/line")
class DomainLine(BaseHandle):
    def get(self, *args, **kwargs):
        sql2 = "select id, line from `lines`;"
        try:
            result = self._db.query(sql2)
            for item in result:
                temp = {}
                temp["value"], temp["label"] = item["id"], item["line"]
                self.response.data.append(temp)
            self.response.code = 20000
            self.response.msg = "查询成功"
            self.response.total = len(result)
        except Exception as e:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(json.dumps(self.response.__dict__))

@router.Route("/domain/add")
class DomainAdd(BaseHandle):
    def post(self, *args, **kwargs):
        print("requestbody: ", self.request_body_data)
        domain_name = self.request_body_data.get("domain_name")
        region = self.request_body_data.get("region") if self.request_body_data.get("region") else "国内"
        domain_type = self.request_body_data.get("domain_type") if self.request_body_data.get("domain_type") else "测试"
        line1 = self.request_body_data.get("line1")
        line2 = self.request_body_data.get("line2")
        line3 = self.request_body_data.get("line3")
        upstreams_list = json.loads(self.request_body_data.get("upstreams"))
        # upstreams_list = self.request_body_data.get("upstreams")
        nginx_upstream_strategy = self.request_body_data.get("function").strip() if self.request_body_data.get("function") else "rr"
        weight = self.request_body_data.get("weight").strip() if self.request_body_data.get("weight") else "1"
        max_fails = self.request_body_data.get("max_fails").strip() if self.request_body_data.get("max_fails") else "3"
        fail_timeout = self.request_body_data.get("fail_timeout").strip() if self.request_body_data.get("fail_timeout") else "10s"
        domain_sql = "select domain_name from domains where domain_type='%s' and domain_name='%s'" % (domain_type, domain_name)
        if self._db.execute_rowcount(domain_sql):
            self.response.code = 50000
            self.response.msg = "记录已存在"
            return self.write(self.response.__dict__)
        if len(domain_name.split('.')) < 2 or ".".join(domain_name.split('.')[-2:]) not in tiger_domain_list:
            self.response.code = 50000
            self.response.msg = "域名不合法"
            return self.write(self.response.__dict__)
        if nginx_upstream_strategy not in tiger_nginxupstream_function_list:
            self.response.code = 50000
            self.response.msg = "upstream算法不合法"
            return self.write(self.response.__dict__)
        upstreams = []
        try:
            for x in upstreams_list:
                if x["ip2"]:
                    upstreams.append(x["ip2"])
                else:
                    raise Exception("upstreams填写不合法")
            # [ upstreams.append(x["ip2"]) for x in upstreams_list ]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "upstreams填写不合法"
            return self.write(self.response.__dict__)
        sql2 = "select id, line from `lines`;"
        nginx_vhosts = {}
        nginx_vhosts["server_name"] = domain_name
        nginx_vhosts["filename"] = domain_name+'.conf'
        nginx_vhosts["ssl_name"] = ".".join(domain_name.split(".")[-2:])

        line_dict = {}
        try:
            result = self._db.query(sql2)
            for item in result:
                line_dict[item["id"]] = item["line"]
            # vip_result = self._db.get("select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1]))
            # vip = vip_result["vip"]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            return self.write(json.dumps(self.response.__dict__))
        print("line_dict:", line_dict)

        if line1 and line2 and line3: # 有三跳
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [host_list.append(x["ip2"]) for x in ips]  # 第一跳需要 同步配置的主机列表
            print("first_jump_host_list: ", host_list)
            nginx_upstream_name_80 = domain_name + "_80"
            nginx_upstream_name_443 = domain_name + "_443"
            next_servers_80 = {}
            next_servers_443 = {}
            next_nginx_servers = []
            next_nginx_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line2])
            ips = self._db.query(next_nginx_server_sql)
            [ next_nginx_servers.append(x["ip2"]) for x in ips ]  # 第一跳中在upstream中填写的下一跳nginx地址
            # total_list = host_list + next_nginx_servers
            next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line2])
            vip = self._db.get(next_nginxvip_server_sql)["vip"]
            # for server in next_nginx_servers:
            next_servers_80[vip + ':80'] = None
            next_servers_443[vip + ':443'] = None
            next_nginx_upstreams = [
                {"name": nginx_upstream_name_80, 'servers': next_servers_80},
                {"name": nginx_upstream_name_443, 'servers': next_servers_443},
            ]
            ext_vars = {"host_list": host_list,
                        'nginx_upstreams': next_nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % host_list)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                last_jump_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line3])
                last_jump_nginx_servers = []
                ips = self._db.query(last_jump_server_sql)
                [ last_jump_nginx_servers.append(x["ip2"]) for x in ips ]

                second_jump_server_80 = {}
                second_jump_server_443 = {}
                second_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line3])
                second_vip = self._db.get(second_nginxvip_server_sql)["vip"]
                # for server in last_jump_nginx_servers:
                second_jump_server_80[second_vip + ':80'] = None
                second_jump_server_443[second_vip + ':443'] = None
                second_nginx_upstream = [
                    {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': second_jump_server_80},
                    {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': second_jump_server_443},
                ]
                ext_vars = {"host_list": next_nginx_servers,
                            # "nginx_upstream_strategy": nginx_upstream_strategy,
                            'nginx_upstreams': second_nginx_upstream,
                            'nginx_vhosts': nginx_vhosts,
                            }
                second_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                              forks=len(next_nginx_servers), ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % next_nginx_servers)
                second_jump_job.run()
                step_2_result = second_jump_job.get_result()  # 至此，2跳nginx涉及的nginx配置已经分发完毕
                if len(step_2_result["success"]) == len(next_nginx_servers):  # 如果所有配置都分发成功
                    last_jump_server_80 = {}
                    last_jump_server_443 = {}
                    for server in upstreams:
                        last_jump_server_80[server + ':80' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                        last_jump_server_443[server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                    last_nginx_upstream = [
                        {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': last_jump_server_80},
                        {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': last_jump_server_443},
                    ]
                    ext_vars = {"host_list": last_jump_nginx_servers,
                                # "nginx_upstream_strategy": nginx_upstream_strategy,
                                'nginx_upstreams': last_nginx_upstream,
                                'nginx_vhosts': nginx_vhosts,
                                }
                    last_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                                    forks=len(last_jump_nginx_servers), ext_vars=ext_vars)
                    print("第三跳配置分发：%s 开始运行" % last_jump_nginx_servers)
                    last_jump_job.run()
                    last_jump_job_result = last_jump_job.get_result()
                    if len(last_jump_job_result["success"]) == len(last_jump_nginx_servers):
                        total_list = host_list + next_nginx_servers + last_jump_nginx_servers
                        ext_vars['cmd'] = "-t"
                        ext_vars["host_list"] = total_list
                        check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                  forks=len(total_list), ext_vars=ext_vars)
                        print("第四步配置检测：%s 开始运行" % total_list)
                        check_job.run()
                        step_4_result = check_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            ext_vars['cmd'] = "-s reload"
                            reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                       forks=len(total_list), ext_vars=ext_vars)
                            print("第五步重启服务：%s 开始运行" % total_list)
                            reload_job.run()
                            step_5_result = reload_job.get_result()
                            print("step 5: ", step_5_result)
                            if len(step_5_result['success']) == len(total_list):
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功"
                                try:
                                    if db_record(self, domain_name, region, domain_type, line1, line2, line3,
                                                 nginx_upstream_strategy, weight, max_fails, fail_timeout,
                                                 upstreams_list):
                                        self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                    else:
                                        self.response.code = 50000
                                        self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                except:
                                    traceback.print_exc()
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                # return self.write(self.response.__dict__)

                            else:
                                self.response.code = 50000
                                self.response.msg = "STEP 5 （重启nginx）失败，请查看执行详情"
                                self.response.data = step_5_result
                                return self.write(self.response.__dict__)
                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （配置检测）失败，请查看执行详情"
                            self.response.data = step_4_result
                            return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （line3分发配置）失败，请查看执行详情"
                        self.response.data = last_jump_job_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)

        elif line1 and line2: # 有两跳
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [ host_list.append(x["ip2"]) for x in ips ] # 第一跳需要 同步配置的主机列表
            print("first_jump_host_list: ", host_list)
            nginx_upstream_name_80 = domain_name+"_80"
            nginx_upstream_name_443 = domain_name+"_443"
            next_servers_80 = {}
            next_servers_443 = {}
            next_nginx_servers = []
            next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line2])
            vip = self._db.get(next_nginxvip_server_sql)["vip"]
            next_nginx_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line2])
            ips = self._db.query(next_nginx_server_sql)
            [next_nginx_servers.append(x["ip2"]) for x in ips] # 第一跳中在upstream中填写的下一跳nginx地址
            total_list = host_list + next_nginx_servers
            # for server in next_nginx_servers:
            next_servers_80[vip + ':80'] = None
            next_servers_443[vip + ':443'] = None
            next_nginx_upstreams = [
                {"name": nginx_upstream_name_80, 'servers': next_servers_80},
                {"name": nginx_upstream_name_443, 'servers': next_servers_443},
            ]
            ext_vars = {"host_list": host_list,
                        'nginx_upstreams': next_nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行"% host_list)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                last_server_80 = {}
                last_server_443 = {}
                for server in upstreams:
                    last_server_80[server + ':80' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                    last_server_443[server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                last_nginx_upstream = [
                    {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': last_server_80},
                    {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': last_server_443},
                ]
                ext_vars = {"host_list": next_nginx_servers,
                            # "nginx_upstream_strategy": nginx_upstream_strategy,
                            'nginx_upstreams': last_nginx_upstream,
                            'nginx_vhosts': nginx_vhosts,
                            }
                last_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(next_nginx_servers),ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % next_nginx_servers)
                last_jump_job.run()
                step_2_result = last_jump_job.get_result() # 至此，2跳nginx涉及的nginx配置已经分发完毕
                if len(step_2_result["success"]) == len(next_nginx_servers): # 如果所有配置都分发成功
                    ext_vars['cmd'] = "-t"
                    ext_vars["host_list"] = total_list
                    check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                              forks=len(total_list), ext_vars=ext_vars)
                    print("第三步配置检测：%s 开始运行" % total_list)
                    check_job.run()
                    step_3_result = check_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(total_list):
                        ext_vars['cmd'] = "-s reload"
                        reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                   forks=len(total_list), ext_vars=ext_vars)
                        print("第四步服务重启：%s 开始运行" % total_list)
                        reload_job.run()
                        step_4_result = reload_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            self.response.code = 20000
                            self.response.msg = "Nginx配置加载全部成功"
                            try:
                                if db_record(self, domain_name, region, domain_type, line1, line2, line3,
                                             nginx_upstream_strategy, weight, max_fails, fail_timeout,
                                             upstreams_list):
                                    self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                else:
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)
                            except:
                                traceback.print_exc()
                                self.response.code = 50000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)

                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （重启nginx）失败，请查看执行详情"
                            self.response.data = step_3_result
                            return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （配置检测）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)

        elif line1: # 只有一跳
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [ host_list.append(x["ip2"]) for x in ips ]
            print("host_list: ", host_list)
            nginx_upstream_name_80 = domain_name+"_80"
            nginx_upstream_name_443 = domain_name+"_443"
            servers_80 = {}
            servers_443 = {}
            for server in upstreams:
                servers_80[server+':80' + ' weight=' + weight + ' max_fails='+max_fails+" fail_timeout="+fail_timeout ] = None
                servers_443[server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
            nginx_upstreams = [
                    {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': servers_80},
                    {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': servers_443},
                ]
            print("nginx_upstream: ", nginx_upstreams)
            ext_vars = {"host_list": host_list,
                        # "nginx_upstream_strategy": nginx_upstream_strategy,
                        'nginx_upstreams': nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list),ext_vars=ext_vars)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                ext_vars['cmd'] = "-t"
                check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                         forks=len(host_list),ext_vars=ext_vars)
                check_job.run()
                step_2_result = check_job.get_result()
                print("step 2: ", step_2_result)
                if len(step_2_result['success']) == len(host_list):
                    ext_vars['cmd'] = "-s reload"
                    reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                         forks=len(host_list),ext_vars=ext_vars)
                    reload_job.run()
                    step_3_result = reload_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(host_list):
                        self.response.code = 20000
                        self.response.msg = "Nginx配置全部加载生效"
                        try:
                            if db_record(self, domain_name, region, domain_type, line1,line2,line3, nginx_upstream_strategy,weight,max_fails,fail_timeout, upstreams_list):
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                return self.write(self.response.__dict__)
                            else:
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)
                        except:
                            traceback.print_exc()
                            self.response.code = 50000
                            self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)

                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （重启nginx）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （配置检测）失败，请查看执行详情"
                    self.response.data = step_2_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)
        else: pass

@router.Route("/domain/update")
class DomainUpdate(BaseHandle):
    def post(self, *args, **kwargs):
        print("requestbody: ", self.request_body_data)
        domain_name = self.request_body_data.get("domain_name")
        region = self.request_body_data.get("region") if self.request_body_data.get("region") else "国内"
        domain_type = self.request_body_data.get("domain_type") if self.request_body_data.get("domain_type") else "测试"
        line1 = self.request_body_data.get("line1")
        line2 = None if self.request_body_data.get("line2") == 6 else self.request_body_data.get("line2")
        line3 = None if self.request_body_data.get("line3") == 6 else self.request_body_data.get("line3")
        upstreams_list = json.loads(self.request_body_data.get("upstreams"))
        # upstreams_list = self.request_body_data.get("upstreams")
        nginx_upstream_strategy = self.request_body_data.get("function") if self.request_body_data.get("function") else "rr"
        weight = self.request_body_data.get("weight") if self.request_body_data.get("weight") else "1"
        max_fails = str(self.request_body_data.get("max_fails")) if self.request_body_data.get("max_fails") else "3"
        fail_timeout = self.request_body_data.get("fail_timeout") if self.request_body_data.get("fail_timeout") else "10s"
        # print(weight, nginx_upstream_strategy, max_fails, fail_timeout)
        # return self.write(self.response.__dict__)
        domain_sql = "select domain_name from domains where domain_type='%s' and domain_name='%s'" % (domain_type, domain_name)
        if not self._db.execute_rowcount(domain_sql):
            self.response.code = 50000
            self.response.msg = "域名不存在"
            return self.write(self.response.__dict__)
        if len(domain_name.split('.')) < 2 or ".".join(domain_name.split('.')[-2:]) not in tiger_domain_list:
            self.response.code = 50000
            self.response.msg = "域名不合法"
            return self.write(self.response.__dict__)
        if nginx_upstream_strategy not in tiger_nginxupstream_function_list:
            self.response.code = 50000
            self.response.msg = "upstream算法不合法"
            return self.write(self.response.__dict__)

        upstreams = []
        try:
            for x in upstreams_list:
                if x["ip2"]:
                    upstreams.append(x["ip2"])
                else:
                    raise Exception("upstreams填写不合法")
            # [ upstreams.append(x["ip2"]) for x in upstreams_list ]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "upstreams填写不合法"
            return self.write(self.response.__dict__)
        sql2 = "select id, line from `lines`;"
        nginx_vhosts = {}
        nginx_vhosts["server_name"] = domain_name
        nginx_vhosts["filename"] = domain_name + '.conf'
        nginx_vhosts["ssl_name"] = ".".join(domain_name.split(".")[-2:])

        line_dict = {}
        try:
            result = self._db.query(sql2)
            for item in result:
                line_dict[item["id"]] = item["line"]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            return self.write(json.dumps(self.response.__dict__))
        print("line_dict:", line_dict)

        if line1 and line2 and line3:  # 有三跳
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [host_list.append(x["ip2"]) for x in ips]  # 第一跳需要 同步配置的主机列表
            print("first_jump_host_list: ", host_list)
            nginx_upstream_name_80 = domain_name + "_80"
            nginx_upstream_name_443 = domain_name + "_443"
            next_servers_80 = {}
            next_servers_443 = {}
            next_nginx_servers = []
            next_nginx_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
            domain_type, line_dict[line2])
            ips = self._db.query(next_nginx_server_sql)
            [next_nginx_servers.append(x["ip2"]) for x in ips]  # 第一跳中在upstream中填写的下一跳nginx地址
            # total_list = host_list + next_nginx_servers
            next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
            domain_type, line_dict[line2])
            vip = self._db.get(next_nginxvip_server_sql)["vip"]
            # for server in next_nginx_servers:
            next_servers_80[vip + ':80'] = None
            next_servers_443[vip + ':443'] = None
            next_nginx_upstreams = [
                {"name": nginx_upstream_name_80, 'servers': next_servers_80},
                {"name": nginx_upstream_name_443, 'servers': next_servers_443},
            ]
            ext_vars = {"host_list": host_list,
                        'nginx_upstreams': next_nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % host_list)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                last_jump_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
                domain_type, line_dict[line3])
                last_jump_nginx_servers = []
                ips = self._db.query(last_jump_server_sql)
                [last_jump_nginx_servers.append(x["ip2"]) for x in ips]

                second_jump_server_80 = {}
                second_jump_server_443 = {}
                second_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
                domain_type, line_dict[line3])
                second_vip = self._db.get(second_nginxvip_server_sql)["vip"]
                # for server in last_jump_nginx_servers:
                second_jump_server_80[second_vip + ':80'] = None
                second_jump_server_443[second_vip + ':443'] = None
                second_nginx_upstream = [
                    {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy,
                     'servers': second_jump_server_80},
                    {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy,
                     'servers': second_jump_server_443},
                ]
                ext_vars = {"host_list": next_nginx_servers,
                            # "nginx_upstream_strategy": nginx_upstream_strategy,
                            'nginx_upstreams': second_nginx_upstream,
                            'nginx_vhosts': nginx_vhosts,
                            }
                second_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                                forks=len(next_nginx_servers), ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % next_nginx_servers)
                second_jump_job.run()
                step_2_result = second_jump_job.get_result()  # 至此，2跳nginx涉及的nginx配置已经分发完毕
                if len(step_2_result["success"]) == len(next_nginx_servers):  # 如果所有配置都分发成功
                    last_jump_server_80 = {}
                    last_jump_server_443 = {}
                    for server in upstreams:
                        last_jump_server_80[
                            server + ':80' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                        last_jump_server_443[
                            server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                    last_nginx_upstream = [
                        {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy,
                         'servers': last_jump_server_80},
                        {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy,
                         'servers': last_jump_server_443},
                    ]
                    ext_vars = {"host_list": last_jump_nginx_servers,
                                # "nginx_upstream_strategy": nginx_upstream_strategy,
                                'nginx_upstreams': last_nginx_upstream,
                                'nginx_vhosts': nginx_vhosts,
                                }
                    last_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                                  forks=len(last_jump_nginx_servers), ext_vars=ext_vars)
                    print("第三跳配置分发：%s 开始运行" % last_jump_nginx_servers)
                    last_jump_job.run()
                    last_jump_job_result = last_jump_job.get_result()
                    if len(last_jump_job_result["success"]) == len(last_jump_nginx_servers):
                        total_list = host_list + next_nginx_servers + last_jump_nginx_servers
                        ext_vars['cmd'] = "-t"
                        ext_vars["host_list"] = total_list
                        check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                  forks=len(total_list), ext_vars=ext_vars)
                        print("第四步配置检测：%s 开始运行" % total_list)
                        check_job.run()
                        step_4_result = check_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            ext_vars['cmd'] = "-s reload"
                            reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                       forks=len(total_list), ext_vars=ext_vars)
                            print("第五步重启服务：%s 开始运行" % total_list)
                            reload_job.run()
                            step_5_result = reload_job.get_result()
                            print("step 5: ", step_5_result)
                            if len(step_5_result['success']) == len(total_list):
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功"
                                try:
                                    if db_update(self, domain_name, region, domain_type, line1, line2, line3,
                                                 nginx_upstream_strategy, weight, max_fails, fail_timeout,
                                                 upstreams_list):
                                        self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                    else:
                                        self.response.code = 50000
                                        self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                except:
                                    traceback.print_exc()
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                    # return self.write(self.response.__dict__)

                            else:
                                self.response.code = 50000
                                self.response.msg = "STEP 5 （重启nginx）失败，请查看执行详情"
                                self.response.data = step_5_result
                                return self.write(self.response.__dict__)
                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （配置检测）失败，请查看执行详情"
                            self.response.data = step_4_result
                            return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （line3分发配置）失败，请查看执行详情"
                        self.response.data = last_jump_job_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)

        elif line1 and line2:  # 有两跳
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [host_list.append(x["ip2"]) for x in ips]  # 第一跳需要 同步配置的主机列表
            print("first_jump_host_list: ", host_list)
            nginx_upstream_name_80 = domain_name + "_80"
            nginx_upstream_name_443 = domain_name + "_443"
            next_servers_80 = {}
            next_servers_443 = {}
            next_nginx_servers = []
            next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
            domain_type, line_dict[line2])
            vip = self._db.get(next_nginxvip_server_sql)["vip"]
            next_nginx_server_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
            domain_type, line_dict[line2])
            ips = self._db.query(next_nginx_server_sql)
            [next_nginx_servers.append(x["ip2"]) for x in ips]  # 第一跳中在upstream中填写的下一跳nginx地址
            total_list = host_list + next_nginx_servers
            # for server in next_nginx_servers:
            next_servers_80[vip + ':80'] = None
            next_servers_443[vip + ':443'] = None
            next_nginx_upstreams = [
                {"name": nginx_upstream_name_80, 'servers': next_servers_80},
                {"name": nginx_upstream_name_443, 'servers': next_servers_443},
            ]
            ext_vars = {"host_list": host_list,
                        'nginx_upstreams': next_nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % host_list)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                last_server_80 = {}
                last_server_443 = {}
                for server in upstreams:
                    last_server_80[
                        server + ':80' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                    last_server_443[
                        server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                last_nginx_upstream = [
                    {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': last_server_80},
                    {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': last_server_443},
                ]
                ext_vars = {"host_list": next_nginx_servers,
                            # "nginx_upstream_strategy": nginx_upstream_strategy,
                            'nginx_upstreams': last_nginx_upstream,
                            'nginx_vhosts': nginx_vhosts,
                            }
                last_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                              forks=len(next_nginx_servers), ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % next_nginx_servers)
                last_jump_job.run()
                step_2_result = last_jump_job.get_result()  # 至此，2跳nginx涉及的nginx配置已经分发完毕
                if len(step_2_result["success"]) == len(next_nginx_servers):  # 如果所有配置都分发成功
                    ext_vars['cmd'] = "-t"
                    ext_vars["host_list"] = total_list
                    check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                              forks=len(total_list), ext_vars=ext_vars)
                    print("第三步配置检测：%s 开始运行" % total_list)
                    check_job.run()
                    step_3_result = check_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(total_list):
                        ext_vars['cmd'] = "-s reload"
                        reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                   forks=len(total_list), ext_vars=ext_vars)
                        print("第四步服务重启：%s 开始运行" % total_list)
                        reload_job.run()
                        step_4_result = reload_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            self.response.code = 20000
                            self.response.msg = "Nginx配置加载全部成功"
                            try:
                                if db_update(self, domain_name, region, domain_type, line1, line2, line3,
                                             nginx_upstream_strategy, weight, max_fails, fail_timeout,
                                             upstreams_list):
                                    self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                else:
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)
                            except:
                                traceback.print_exc()
                                self.response.code = 50000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)

                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （重启nginx）失败，请查看执行详情"
                            self.response.data = step_3_result
                            return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （配置检测）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)

        elif line1:  # 只有一跳
            print("只有一跳")
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            print("sql: ", sql)
            ips = self._db.query(sql)
            host_list = []
            [host_list.append(x["ip2"]) for x in ips]
            print("host_list: ", host_list)
            nginx_upstream_name_80 = domain_name + "_80"
            nginx_upstream_name_443 = domain_name + "_443"
            servers_80 = {}
            servers_443 = {}
            for server in upstreams:
                servers_80[
                    server + ':80' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
                servers_443[
                    server + ':443' + ' weight=' + weight + ' max_fails=' + max_fails + " fail_timeout=" + fail_timeout] = None
            nginx_upstreams = [
                {"name": nginx_upstream_name_80, 'strategy': nginx_upstream_strategy, 'servers': servers_80},
                {"name": nginx_upstream_name_443, 'strategy': nginx_upstream_strategy, 'servers': servers_443},
            ]
            print("nginx_upstream: ", nginx_upstreams)
            ext_vars = {"host_list": host_list,
                        # "nginx_upstream_strategy": nginx_upstream_strategy,
                        'nginx_upstreams': nginx_upstreams,
                        'nginx_vhosts': nginx_vhosts,
                        }
            one_jump_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/generate_nginx_vhost.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            one_jump_job.run()
            step_1_result = one_jump_job.get_result()
            if len(step_1_result["success"]) == len(host_list):
                ext_vars['cmd'] = "-t"
                check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                          forks=len(host_list), ext_vars=ext_vars)
                check_job.run()
                step_2_result = check_job.get_result()
                print("step 2: ", step_2_result)
                if len(step_2_result['success']) == len(host_list):
                    ext_vars['cmd'] = "-s reload"
                    reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                               forks=len(host_list), ext_vars=ext_vars)
                    reload_job.run()
                    step_3_result = reload_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(host_list):
                        self.response.code = 20000
                        self.response.msg = "Nginx配置全部加载生效"
                        try:
                            if db_update(self, domain_name, region, domain_type, line1, line2, line3,
                                         nginx_upstream_strategy, weight, max_fails, fail_timeout, upstreams_list):
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                            else:
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)
                        except:
                            traceback.print_exc()
                            self.response.code = 50000
                            self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)

                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （重启nginx）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （配置检测）失败，请查看执行详情"
                    self.response.data = step_2_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "STEP 1 （分发配置）失败，请查看执行详情"
                self.response.data = step_1_result
                return self.write(self.response.__dict__)
        else:
            pass



@router.Route("/domain/delete")
class DomainDelete(BaseHandle):
    def post(self, *args, **kwargs):
        domain_id = self.request_body_data.get("domain_id")[0]
        sql = "select id, line from `lines`;"
        line_dict = {}
        try:
            result = self._db.query(sql)
            for item in result:
                line_dict[item["id"]] = item["line"]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            return self.write(self.response.__dict__)
        try:
            sql2 = "select domain_name, domain_type, line1, line2, line3 from domains where domain_id='%s';" % domain_id
            print(sql2)
            domain_info = self._db.get(sql2)
        except:
            self.response.msg = "ID错误"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        print("domain_info: %s "% domain_info)
        # self.write(self.response.__dict__)
        domain_name = domain_info["domain_name"]
        domain_type = domain_info["domain_type"]
        line1 = domain_info["line1"]
        line2 = domain_info["line2"]
        line3 = domain_info["line3"]

        cfgfile = os.path.join(nginx_vhost_path , domain_name + ".conf")
        print(cfgfile)
        # return self.write(self.response.__dict__)
        try:
            sql = "select ip2 from nginx where server_type='%s' and idc in ('%s', '%s', '%s')" % (domain_type, str(line_dict.get(line1, None)),
                                                                                                  str(line_dict.get(line2, None)), str(line_dict.get(line3, None)))

            ips = self._db.query(sql)
            host_list = []
            [ host_list.append(x["ip2"]) for x in ips ]

        except:
            self.response.msg = "后端错误"
            self.response.code = 50000
            return self.write(self.response.__dict__)

        ext_vars = {"host_list": host_list, "cfgfile": cfgfile}
        del_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/remove_nginx_proxycfg.yml",
                                     forks=len(host_list), ext_vars=ext_vars)
        print("配置删除开始: ", host_list)
        del_job.run()
        del_result = del_job.get_result()
        if len(del_result["success"]) == len(host_list):
            ext_vars["cmd"] = "-t"
            configtest_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                     forks=len(host_list), ext_vars=ext_vars)
            configtest_job.run()
            config_result = configtest_job.get_result()
            if len(config_result["success"]) == len(host_list):
                ext_vars["cmd"] = "-s reload"
                reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                               forks=len(host_list), ext_vars=ext_vars)
                reload_job.run()
                reload_result = reload_job.get_result()
                if len(reload_result["success"]) == len(host_list):
                    if db_delete(self, domain_id):
                        self.response.code = 20000
                        self.response.msg = "域名记录删除成功"
                    else:
                        self.response.code = 50000
                        self.response.msg = "域名记录删除失败"
                    return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "节点重启失败失败"
                    self.response.data = reload_result
                    return self.write(self.response.__dict__)
            else:
                self.response.code = 50000
                self.response.msg = "配置检测失败"
                self.response.data = config_result
                return self.write(self.response.__dict__)
        else:
            self.response.code = 50000
            self.response.msg = "域名删除失败"
            self.response.data = del_result
            return self.write(self.response.__dict__)

example_list = [
    {
        "nginx_upstreams": [
            {
                "name": "www.itiger.com_80",
                "servers": ["42.200.38.121:80"],
                "keepalive": None,
                "strategy": "rr",
            },
            {
                "name": "www.itiger.com_443",
                "servers": ["42.200.38.121:443"],
                "keepalive": None,
                "strategy": "rr",
            },
        ],
        "nginx_vhosts": {
            "server_name": "www.itiger.com",
            "ssl_name": "itiger.com.pem",
        }
    },
]
@router.Route("/domain/multiupdate")
class DomainMultiUpdate(BaseHandle):
    def get_domain_variables(self, domain_name, varables):
        step = varables[0]
        line1 = varables[1]
        line2 = varables[2]
        line3 = varables[3]
        line_dict = varables[4]
        domain_type = varables[5]
        # print(varables)
        temp_dict = {}
        temp_dict["nginx_upstreams"] = []
        temp_dict["nginx_vhosts"] = {
            "server_name": domain_name,
            "ssl_name": ".".join(domain_name.split(".")[-2:]),
            "filename": domain_name + ".conf",
        }
        if step == 1:
            if line3 and line2 and line1:
                next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
                    domain_type, line_dict[line2])
                vip = self._db.get(next_nginxvip_server_sql)["vip"]
                temp_dict["nginx_upstreams"] = [
                            {
                                "name": domain_name + "_80",
                                "servers": [vip+":80"],
                                "keepalive": None,
                                "strategy": "rr",
                            },
                            {
                                "name": domain_name + "_443",
                                "servers": [vip+":443"],
                                "keepalive": None,
                                "strategy": "rr",
                            },
                        ]
                return temp_dict

            elif line2 and line1:
                next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
                    domain_type, line_dict[line2])
                vip = self._db.get(next_nginxvip_server_sql)["vip"]
                # for server in next_nginx_servers:
                temp_dict["nginx_upstreams"] = [
                    {
                        "name": domain_name + "_80",
                        "servers": [vip + ":80"],
                        "keepalive": None,
                        "strategy": "rr",
                    },
                    {
                        "name": domain_name + "_443",
                        "servers": [vip + ":443"],
                        "keepalive": None,
                        "strategy": "rr",
                    },
                ]

                return temp_dict
            elif line1:
                domain_id_sql = "select domain_id from domains where domain_name='%s' and domain_type='%s'" % (
                    domain_name, domain_type)
                domain_id = self._db.get(domain_id_sql)["domain_id"]
                select_upstream_sql = "select ip2, port, function, weight, max_fails, fail_timeout from upstream_server where domain_id=%d;" % domain_id
                backend_servers = self._db.query(select_upstream_sql)
                tmp_80_servers = []
                tmp_443_servers = []
                tmp_80_dict = {}
                tmp_443_dict = {}
                for backend_server in backend_servers:
                    tmp_80_servers.append(backend_server["ip2"] + ':80' + ' weight=' + str(backend_server["weight"])
                                          + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                          backend_server["fail_timeout"])
                    tmp_443_servers.append(backend_server["ip2"] + ':443' + ' weight=' + str(backend_server["weight"])
                                           + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                           backend_server["fail_timeout"])
                tmp_80_dict["name"] = domain_name + "_80"
                tmp_80_dict["strategy"] = backend_servers[0]["function"]
                tmp_80_dict["servers"] = tmp_80_servers
                tmp_443_dict["name"] = domain_name + "_443"
                tmp_443_dict["strategy"] = backend_servers[0]["function"]
                tmp_443_dict["servers"] = tmp_443_servers
                temp_dict["nginx_upstreams"].append(tmp_80_dict)
                temp_dict["nginx_upstreams"].append(tmp_443_dict)
                return temp_dict
            else:pass

        if step == 2:
            if line3 and line2 and line1:
                next_nginxvip_server_sql = "select DISTINCT(vip) from nginx where server_type='%s' and idc='%s'" % (
                    domain_type, line_dict[line3])
                vip = self._db.get(next_nginxvip_server_sql)["vip"]
                temp_dict["nginx_upstreams"] = [
                    {
                        "name": domain_name + "_80",
                        "servers": [vip + ":80"],
                        "keepalive": None,
                        "strategy": "rr",
                    },
                    {
                        "name": domain_name + "_443",
                        "servers": [vip + ":443"],
                        "keepalive": None,
                        "strategy": "rr",
                    },
                ]
                return temp_dict

            elif line2 and line1:
                domain_id_sql = "select domain_id from domains where domain_name='%s' and domain_type='%s'" % (
                    domain_name, domain_type)
                domain_id = self._db.get(domain_id_sql)["domain_id"]
                select_upstream_sql = "select ip2, port, function, weight, max_fails, fail_timeout from upstream_server where domain_id=%d;" % domain_id
                backend_servers = self._db.query(select_upstream_sql)
                tmp_80_servers = []
                tmp_443_servers = []
                tmp_80_dict = {}
                tmp_443_dict = {}
                for backend_server in backend_servers:
                    tmp_80_servers.append(backend_server["ip2"] + ':80' + ' weight=' + str(backend_server["weight"])
                                          + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                          backend_server["fail_timeout"])
                    tmp_443_servers.append(backend_server["ip2"] + ':443' + ' weight=' + str(backend_server["weight"])
                                           + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                           backend_server["fail_timeout"])
                tmp_80_dict["name"] = domain_name + "_80"
                tmp_80_dict["strategy"] = backend_servers[0]["function"]
                tmp_80_dict["servers"] = tmp_80_servers
                tmp_443_dict["name"] = domain_name + "_443"
                tmp_443_dict["strategy"] = backend_servers[0]["function"]
                tmp_443_dict["servers"] = tmp_443_servers
                temp_dict["nginx_upstreams"].append(tmp_80_dict)
                temp_dict["nginx_upstreams"].append(tmp_443_dict)
                return temp_dict
            else:
                pass

        if step == 3:
            domain_id_sql = "select domain_id from domains where domain_name='%s' and domain_type='%s'" % (
                domain_name, domain_type)
            domain_id = self._db.get(domain_id_sql)["domain_id"]
            select_upstream_sql = "select ip2, port, function, weight, max_fails, fail_timeout from upstream_server where domain_id=%d;" % domain_id
            backend_servers = self._db.query(select_upstream_sql)
            tmp_80_servers = []
            tmp_443_servers = []
            tmp_80_dict = {}
            tmp_443_dict = {}
            for backend_server in backend_servers:
                tmp_80_servers.append(backend_server["ip2"] + ':80' + ' weight=' + str(backend_server["weight"])
                                                     + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                                     backend_server["fail_timeout"])
                tmp_443_servers.append(backend_server["ip2"] + ':443' + ' weight=' + str(backend_server["weight"])
                                                     + ' max_fails=' + str(backend_server["max_fails"]) + " fail_timeout=" +
                                       backend_server["fail_timeout"])
            tmp_80_dict["name"] = domain_name + "_80"
            tmp_80_dict["strategy"] = backend_servers[0]["function"]
            tmp_80_dict["servers"] = tmp_80_servers
            tmp_443_dict["name"] = domain_name + "_443"
            tmp_443_dict["strategy"] = backend_servers[0]["function"]
            tmp_443_dict["servers"] = tmp_443_servers
            temp_dict["nginx_upstreams"].append(tmp_80_dict)
            temp_dict["nginx_upstreams"].append(tmp_443_dict)
            return temp_dict
        exit()

    def post(self, *args, **kwargs):
        print("requestbody: ", self.request_body_data)
        region = self.request_body_data.get("region") if self.request_body_data.get("region") else "国内"
        domain_type = self.request_body_data.get("domain_type") if self.request_body_data.get(
            "domain_type") else "测试"
        line1 = self.request_body_data.get("line1")
        line2 = self.request_body_data.get("line2")
        line3 = self.request_body_data.get("line3")
        domain_list = self.request_body_data.get("domainList")
        for domain_name in domain_list:
            domain_sql = "select domain_name from domains where domain_type='%s' and domain_name='%s'" % (
        domain_type, domain_name)
            if not self._db.execute_rowcount(domain_sql):
                self.response.code = 50000
                self.response.msg = "域名不存在"
                return self.write(self.response.__dict__)
            if len(domain_name.split('.')) < 2 or ".".join(domain_name.split('.')[-2:]) not in tiger_domain_list:
                self.response.code = 50000
                self.response.msg = "域名不合法"
                return self.write(self.response.__dict__)

        sql2 = "select id, line from `lines`;"
        line_dict = {}
        try:
            result = self._db.query(sql2)
            for item in result:
                line_dict[item["id"]] = item["line"]
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            return self.write(json.dumps(self.response.__dict__))
        print("line_dict:", line_dict)
        if line1 and line2 and line3:  # 有三跳
            step = 1
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            ips = self._db.query(sql)
            host_list = []
            [ host_list.append(x["ip2"]) for x in ips ]  # 第一跳需要 同步配置的主机列表
            varables_list = []
            for item in domain_list:
                tmp_list = []
                tmp_list.append(step)
                tmp_list.append(line1)
                tmp_list.append(line2)
                tmp_list.append(line3)
                tmp_list.append(line_dict)
                tmp_list.append(domain_type)
                varables_list.append(tmp_list)
            my_list = map(self.get_domain_variables, domain_list, varables_list)
            # print(list(my_list))
            # return self.write(json.dumps(self.response.__dict__))
            ext_vars = {"host_list": host_list, "my_list": list(my_list)}
            one_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                         forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % host_list)
            step_1_result = one_jump_job.run()
            success = True
            for host in host_list:
                if step_1_result["stats"][host]['ok'] != 1:
                    self.response.code = 50000
                    self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            if success:
                step = 2
                second_jump_nginxips_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
                    domain_type, line_dict[line2])
                second_jump_nginxips = []
                ips = self._db.query(second_jump_nginxips_sql)
                [second_jump_nginxips.append(x["ip2"]) for x in ips] # 获取第二跳需要配置的nginx地址
                varables_list = []
                for item in domain_list:
                    tmp_list = []
                    tmp_list.append(step)
                    tmp_list.append(line1)
                    tmp_list.append(line2)
                    tmp_list.append(line3)
                    tmp_list.append(line_dict)
                    tmp_list.append(domain_type)
                    varables_list.append(tmp_list)
                my_list = map(self.get_domain_variables, domain_list, varables_list)
                ext_vars = {"host_list": second_jump_nginxips, "my_list": list(my_list)}
                print(ext_vars)
                second_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                                forks=len(second_jump_nginxips), ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % second_jump_nginxips)
                step_2_result = second_jump_job.run() # 至此，2跳nginx涉及的nginx配置已经分发完毕
                for host in second_jump_nginxips:
                    if step_2_result["stats"][host]['ok'] != 1:
                        self.response.code = 50000
                        self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                        self.response.data = step_2_result
                        return self.write(self.response.__dict__)
                if success:
                    step = 3
                    last_jump_nginxips_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
                        domain_type, line_dict[line3])
                    last_jump_nginxips = []
                    ips = self._db.query(last_jump_nginxips_sql)
                    [last_jump_nginxips.append(x["ip2"]) for x in ips]  # 获取第二跳需要配置的nginx地址
                    varables_list = []
                    for item in domain_list:
                        tmp_list = []
                        tmp_list.append(step)
                        tmp_list.append(line1)
                        tmp_list.append(line2)
                        tmp_list.append(line3)
                        tmp_list.append(line_dict)
                        tmp_list.append(domain_type)
                        varables_list.append(tmp_list)
                    my_list = map(self.get_domain_variables, domain_list, varables_list)
                    ext_vars = {"host_list": last_jump_nginxips, "my_list": list(my_list)}
                    print(ext_vars)
                    last_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                                  forks=len(last_jump_nginxips), ext_vars=ext_vars)
                    print("第三跳配置分发：%s 开始运行" % last_jump_nginxips)
                    step_3_result = last_jump_job.run()
                    for host in last_jump_nginxips:
                        if step_3_result["stats"][host]['ok'] != 1:
                            self.response.code = 50000
                            self.response.msg = "STEP 3 （line3分发配置）失败，请查看执行详情"
                            self.response.data = step_3_result
                            return self.write(self.response.__dict__)
                    if success:
                        print("第三跳配置分发成功")
                        total_list = host_list + second_jump_nginxips + last_jump_nginxips
                        ext_vars['cmd'] = "-t"
                        ext_vars["host_list"] = total_list
                        check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                  forks=len(total_list), ext_vars=ext_vars)
                        print("第四步配置检测：%s 开始运行" % total_list)
                        check_job.run()
                        step_4_result = check_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            ext_vars['cmd'] = "-s reload"
                            reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                       forks=len(total_list), ext_vars=ext_vars)
                            print("第五步重启服务：%s 开始运行" % total_list)
                            reload_job.run()
                            step_5_result = reload_job.get_result()
                            print("step 5: ", step_5_result)
                            if len(step_5_result['success']) == len(total_list):
                                self.response.code = 20000
                                self.response.msg = "Nginx配置加载全部成功"
                                try:
                                    if db_multi_update(self, domain_list, line1, line2, line3, region):
                                        self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                    else:
                                        self.response.code = 50000
                                        self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                except:
                                    traceback.print_exc()
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                    return self.write(self.response.__dict__)
                                    # return self.write(self.response.__dict__)
                            else:
                                self.response.code = 50000
                                self.response.msg = "STEP 5 （重启nginx）失败，请查看执行详情"
                                self.response.data = step_5_result
                                return self.write(self.response.__dict__)
                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （配置检测）失败，请查看执行详情"
                            self.response.data = step_4_result
                            return self.write(self.response.__dict__)

        elif line1 and line2:  # 有两跳
            step = 1
            total_list = []
            sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (domain_type, line_dict[line1])
            ips = self._db.query(sql)
            host_list = []
            [host_list.append(x["ip2"]) for x in ips]  # 第一跳需要 同步配置的主机列表
            varables_list = []
            for item in domain_list:
                tmp_list = []
                tmp_list.append(step)
                tmp_list.append(line1)
                tmp_list.append(line2)
                tmp_list.append(line3)
                tmp_list.append(line_dict)
                tmp_list.append(domain_type)
                varables_list.append(tmp_list)
            my_list = map(self.get_domain_variables, domain_list, varables_list)

            ext_vars = {"host_list": host_list, "my_list": list(my_list)}
            one_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                          forks=len(host_list), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % host_list)
            step_1_result = one_jump_job.run()
            success = True
            for host in host_list:
                if step_1_result["stats"][host]['ok'] != 1:
                    self.response.code = 50000
                    self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            if success:
                step = 2
                second_jump_nginxips_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
                    domain_type, line_dict[line2])
                second_jump_nginxips = []
                ips = self._db.query(second_jump_nginxips_sql)
                [second_jump_nginxips.append(x["ip2"]) for x in ips]  # 获取第二跳需要配置的nginx地址
                varables_list = []
                for item in domain_list:
                    tmp_list = []
                    tmp_list.append(step)
                    tmp_list.append(line1)
                    tmp_list.append(line2)
                    tmp_list.append(line3)
                    tmp_list.append(line_dict)
                    tmp_list.append(domain_type)
                    varables_list.append(tmp_list)
                my_list = map(self.get_domain_variables, domain_list, varables_list)
                ext_vars = {"host_list": second_jump_nginxips, "my_list": list(my_list)}
                print(ext_vars)
                second_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                                 forks=len(second_jump_nginxips), ext_vars=ext_vars)
                print("第二跳配置分发：%s 开始运行" % second_jump_nginxips)
                step_2_result = second_jump_job.run()  # 至此，2跳nginx涉及的nginx配置已经分发完毕
                for host in second_jump_nginxips:
                    if step_2_result["stats"][host]['ok'] != 1:
                        self.response.code = 50000
                        self.response.msg = "STEP 2 （line2分发配置）失败，请查看执行详情"
                        self.response.data = step_2_result
                        return self.write(self.response.__dict__)
                if success:
                    step = 3
                    total_list = host_list + second_jump_nginxips
                    ext_vars['cmd'] = "-t"
                    ext_vars["host_list"] = total_list
                    check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                              forks=len(total_list), ext_vars=ext_vars)
                    print("第三步配置检测：%s 开始运行" % total_list)
                    check_job.run()
                    step_3_result = check_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(total_list):
                        ext_vars['cmd'] = "-s reload"
                        reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                                   forks=len(total_list), ext_vars=ext_vars)
                        print("第四步重启服务：%s 开始运行" % total_list)
                        reload_job.run()
                        step_4_result = reload_job.get_result()
                        print("step 4: ", step_4_result)
                        if len(step_4_result['success']) == len(total_list):
                            self.response.code = 20000
                            self.response.msg = "Nginx配置加载全部成功"
                            try:
                                if db_multi_update(self, domain_list, line1, line2, line3, region):
                                    self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                                else:
                                    self.response.code = 50000
                                    self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)
                            except:
                                traceback.print_exc()
                                self.response.code = 50000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                                return self.write(self.response.__dict__)
                                # return self.write(self.response.__dict__)
                        else:
                            self.response.code = 50000
                            self.response.msg = "STEP 4 （重启nginx）失败，请查看执行详情"
                            self.response.data = step_4_result
                            return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （配置检测）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
        elif line1:  # 只有一跳
            success = True
            step = 1
            second_jump_nginxips_sql = "select ip2 from nginx where server_type='%s' and idc='%s'" % (
                domain_type, line_dict[line1])
            second_jump_nginxips = []
            ips = self._db.query(second_jump_nginxips_sql)
            [second_jump_nginxips.append(x["ip2"]) for x in ips]  # 获取第二跳需要配置的nginx地址
            varables_list = []
            for item in domain_list:
                tmp_list = []
                tmp_list.append(step)
                tmp_list.append(line1)
                tmp_list.append(line2)
                tmp_list.append(line3)
                tmp_list.append(line_dict)
                tmp_list.append(domain_type)
                varables_list.append(tmp_list)
            my_list = map(self.get_domain_variables, domain_list, varables_list)
            ext_vars = {"host_list": second_jump_nginxips, "my_list": list(my_list)}
            print(ext_vars)
            second_jump_job = NewPlayBookAPI(playbooks="backend/playbook_jobs/generate_multiconf.yml",
                                             forks=len(second_jump_nginxips), ext_vars=ext_vars)
            print("第一跳配置分发：%s 开始运行" % second_jump_nginxips)
            step_1_result = second_jump_job.run()  # 至此，2跳nginx涉及的nginx配置已经分发完毕
            for host in second_jump_nginxips:
                if step_1_result["stats"][host]['ok'] != 1:
                    self.response.code = 50000
                    self.response.msg = "STEP 1 （line1分发配置）失败，请查看执行详情"
                    self.response.data = step_1_result
                    return self.write(self.response.__dict__)
            if success:
                total_list = second_jump_nginxips
                ext_vars['cmd'] = "-t"
                ext_vars["host_list"] = total_list
                check_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                          forks=len(total_list), ext_vars=ext_vars)
                print("第二步配置检测：%s 开始运行" % total_list)
                check_job.run()
                step_2_result = check_job.get_result()
                print("step 2: ", step_2_result)
                if len(step_2_result['success']) == len(total_list):
                    ext_vars['cmd'] = "-s reload"
                    reload_job = MyPlayBookAPI(playbooks="backend/playbook_jobs/execute_nginx_cmd.yml",
                                               forks=len(total_list), ext_vars=ext_vars)
                    print("第三步重启服务：%s 开始运行" % total_list)
                    reload_job.run()
                    step_3_result = reload_job.get_result()
                    print("step 3: ", step_3_result)
                    if len(step_3_result['success']) == len(total_list):
                        self.response.code = 20000
                        self.response.msg = "Nginx配置加载全部成功"
                        try:
                            if db_multi_update(self, domain_list, line1, line2, line3, region):
                                self.response.msg = "Nginx配置加载全部成功,且记录成功入库"
                            else:
                                self.response.code = 50000
                                self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)
                        except:
                            traceback.print_exc()
                            self.response.code = 50000
                            self.response.msg = "Nginx配置加载全部成功,但记录入库失败"
                            return self.write(self.response.__dict__)
                            # return self.write(self.response.__dict__)
                    else:
                        self.response.code = 50000
                        self.response.msg = "STEP 3 （重启nginx）失败，请查看执行详情"
                        self.response.data = step_3_result
                        return self.write(self.response.__dict__)
                else:
                    self.response.code = 50000
                    self.response.msg = "STEP 2 （配置检测）失败，请查看执行详情"
                    self.response.data = step_2_result
                    return self.write(self.response.__dict__)
        else:
            pass

@router.Route("/domain/getbyidc")
class GetDomainByIDC(BaseHandle):
    def get(self, *args, **kwargs):
        idc = self.get_argument("id")
        domain_type = self.get_argument("domain_type", '测试')
        region = self.get_argument("region", '国内')
        sql2 = "select domain_name from domains where line3='%s' and domain_type='%s' and region='%s' or line3 is NULL and line2='%s' and domain_type='%s' and region='%s'" \
               " or line2 is NULL and line1='%s' and domain_type='%s' and region='%s';" % (idc, domain_type,region,idc,domain_type, region,idc, domain_type, region)
        try:
            domain_dicts = self._db.query(sql2)
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            return self.write(json.dumps(self.response.__dict__))
        for domain in domain_dicts:
            self.response.data.append(domain["domain_name"])
        self.response.code = 20000
        self.response.msg = "查询成功"
        self.response.total = len(domain_dicts)
        return self.write(self.response.__dict__)