#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 11:22
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: nginxserver.py


import json
import traceback
import requests
import datetime
import router
# from backend.test.test2 import PlayBookJob
from backend.ansible_api.playbook import MyPlayBookAPI
from config import nginx_configtest_ok_flag, keepalive_restart_ok_flag
from handle.base import BaseHandle
from libs.utils import CJsonEncoder


@router.Route("/nginx/getAll")
class NginxGetAll(BaseHandle):
    def get(self, *args, **kwargs):
        page = self.get_argument("page")
        page_size = self.get_argument("pagesize")
        page_start = (int(page) - 1) * int(page_size)
        limitsize = int(page_size)
        sql2 = "select server_id, idc, vip, ip1, ip2, role,server_type from nginx limit %d, %d;"
        try:
            result = self._db.query(sql2 % (page_start, limitsize))
            self.response.code = 20000
            self.response.data = result
            self.response.total = len(result)
        except Exception as e:
            print(e)
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(json.dumps(self.response.__dict__, cls=CJsonEncoder))


@router.Route("/nginx/add")  # finish
class NginxAdd(BaseHandle):
    def post(self, *args, **kwargs):
        sn = self.request_body_data.get('sn')
        # 根据SN获取nginx服务器的配置信息
        print("sn:", self.request_body_data)
        try:
            url='http://cmdb.tigerbrokers.net:8000/public/getAll'
            res = requests.post(url, data=json.dumps({"lhzq_sn": sn}))
            res = res.json()
            res_data = res['data']
            if res.get("code") != "20000":
                self.response.msg = "资产不存在"
                self.response.code = 50000
                return self.write(self.response.__dict__)
        except:
            traceback.print_exc()
            self.response.msg = "后端错误"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        try:
            ip2 = res_data.get("ip2")
        except:
            traceback.print_exc()
            self.response.msg = "资产编号错误"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        ip1 = ip2 if not res_data.get("ip1") else res_data.get("ip1")
        idc = res_data.get("isp")
        vip = self.request_body_data.get('vip','')
        role = self.request_body_data.get('role', 'backup')
        server_type = self.request_body_data.get('server_type', 'test')
        sql = "insert into nginx (`lhzq_sn`,`idc`,`vip`,`ip1`,`ip2`, `role`, `server_type`, `last_editor`)  VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s');"
        # sql1='select vm_sn from vm union all select lhzq_sn from device;'
        try:
            self._db.insert(sql % (sn, idc, vip, ip1, ip2, role, server_type, self.current_user))
            self.response.code = 20000
            self.response.msg = "添加成功"
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(self.response.__dict__)

@router.Route("/nginx/update")
class NginxUpdate(BaseHandle):
    def post(self, *args, **kwargs):
        id = self.request_body_data.get("id")
        sn = self.request_body_data.get('sn')
        try:
            url='http://cmdb.tigerbrokers.net:8000/public/getAll'
            res = requests.post(url, data=json.dumps({"lhzq_sn": sn}))
            res = res.json()
            res_data = res['data']
            if res.get("code") != "20000":
                self.response.msg = "资产不存在"
                self.response.code = 50000
                return self.write(self.response.__dict__)
        except:
            traceback.print_exc()
            self.response.msg = "后端错误"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        ip2 = res_data.get("ip2")
        ip1 = ip2 if not res_data.get("ip1") else res_data.get("ip1")
        idc = res_data.get("isp")
        vip = self.request_body_data.get('vip', '')
        role = self.request_body_data.get('role', '')
        server_type = self.request_body_data.get('server_type', 'test')

        sql = "update nginx set `lhzq_sn`=%s, idc=%s, vip=%s, ip1=%s, ip2=%s, role=%s, server_type=%s, last_editor=%s where server_id=%s;"
        try:
            self._db.update(sql % (sn, idc, vip, ip1, ip2, role, server_type, self.current_user, id))
            self.response.code = 20000
            self.response.msg = "修改成功"
        except:
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(self.response.__dict__)


@router.Route("/nginx/delete")
class NginxDelete(BaseHandle):
    def post(self, *args, **kwargs):
        id = self.request_body_data.get("id")
        id = '(' + ','.join(map(str, id)) + ')'
        sql = "delete from nginx where server_id in %s;"
        try:
            self._db.execute(sql % id)
            self.response.code = 20000
            self.response.msg = "删除成功"
        except:
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(self.response.__dict__)

@router.Route("/nginx/cmd")
class NginxCmd(BaseHandle):
    def post(self, *args, **kwargs):
        id = self.request_body_data.get("id")
        action = self.request_body_data.get("action")
        action_dict = {
            "configtest": "-t",
            "restart": "-s reload",
            "change": "restart", # 控制keepalived
        }
        id = '(' + ','.join(map(str, id)) + ')'

        if action == "change":
            sql = "select ip2 from nginx where vip in (select vip from nginx where server_id in %s) and role='master';"
        else:
            sql = "select ip2 from nginx where server_id in %s;"
        try:
            host_list = []
            ips = self._db.query(sql % id)
            print("ips sql:", sql % id)
            [ host_list.append(x["ip2"]) for x in ips ]
            print(host_list)
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            self.write(self.response.__dict__)

        ext_vars = {"host_list": host_list, 'cmd':action_dict[action]}
        print("ext_vars: ", ext_vars)
        try:
            if action == "change":
                job = MyPlayBookAPI(playbooks='backend/playbook_jobs/change_nginx_role_manual.yml',
                                  ssh_user='lhop',
                                  ext_vars=ext_vars)
            else:
                job = MyPlayBookAPI(playbooks='backend/playbook_jobs/execute_nginx_cmd.yml',
                                  ssh_user='lhop',
                                  ext_vars=ext_vars)
            job.run()
            request_content = job.get_result()
            print("回应的数据： ", request_content)
            if request_content['failed'] and request_content["unreachable"]:
                self.response.code = 50000
                self.response.msg = "执行失败"
                self.response.data.append(request_content)
                # return self.write(self.response.__dict__)
            elif len(list(request_content["success"].keys())) == len(host_list):
                self.response.code = 20000
                self.response.msg = "执行成功"
                self.response.data.append(request_content)
            else: pass
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
        finally:
            try:
                if action == "change" and self.response.code == 20000:
                    ips_sql = "select ip2 from nginx where vip in (select vip from nginx where server_id in %s)"
                    print("Update DB ")
                    ips_dict_list = self._db.query(ips_sql % id)
                    ips_list = []
                    [ ips_list.append(x["ip2"]) for x in ips_dict_list ]
                    print('change role status list:', ips_list)
                    update_sql = "UPDATE  nginx AS n1 JOIN nginx AS n2 ON (n1.ip2 = '%s' AND n2.ip2 = '%s') " \
                                 "SET n1.role = n2.role, n2.role = n1.role, n1.last_editor='%s', n2.last_editor='%s';" % (ips_list[0], ips_list[1], self.current_user, self.current_user)
                    print(update_sql)
                    self._db.execute(update_sql)
            except:
                traceback.print_exc()
                self.response.msg = "后端状态变更错误,请手动更正"
                self.response.code = 50000

            return self.write(self.response.__dict__)


# @router.Route("/nginx/status")
# class NginxStatus(BaseHandle):
#     # @coroutine
#     def post(self, *args, **kwargs):
#         # 支持connect|request
#         id = self.request_body_data.get("id")
#         id = '(' + ','.join(map(str, id)) + ')'
#         action = self.request_body_data.get("action")
#         host_list = []
#         sql = "select ip2 from nginx where server_id in %s;"
#         try:
#             ips = self._db.query(sql % id)
#             [ host_list.append(x["ip2"]) for x in ips ]
#         except:
#             traceback.print_exc()
#             self.response.code = 50000
#             self.response.msg = "后端错误"
#         ext_vars = {"host_list": host_list}
#
#         if action == "connect":
#             job = MyPlayBookAPI(playbooks=['backend/playbook_jobs/get_remote_tcpconnection.yml'],
#                               ssh_user='lhop',
#                               ext_vars=ext_vars)
#             job.run()
#             request_content = job.get_result()
#             print('request_content: ', request_content)
#             '''
#              {'172.28.48.6': ['LAST-ACK 79', 'SYN-RECV 17',
#              'ESTAB 3083', 'FIN-WAIT-1 83', 'CLOSING 18', 'FIN-WAIT-2 888', 'TIME-WAIT 12502', 'LISTEN 7']}
#             '''
#
#             for host, value_list in request_content.items():
#                 host_status = {}
#                 host_status["server_ip"] = host
#                 for value in value_list:
#                     k,v = value.split(' ')
#                     host_status[k] = v
#                 self.response.data.append(host_status)
#             self.response.code = 20000
#             self.response.msg = "查询成功"
#
#         elif action == "request":
#             job = MyPlayBookAPI(playbooks=['backend/get_nginx_request_status.yml'],
#                               ssh_user='lhop',
#                               ext_vars=ext_vars)
#             print('job request finished')
#             # print(dir(job))
#             request_content = job.run()
#             print('request_content: ', request_content)
#             '''
#             {'172.28.48.6': ['Active connections: 4706 ', 'server accepts handled requests',
#                              ' 1107496568 1107496568 5010900395 ', 'Reading: 0 Writing: 18 Waiting: 4046 '],
#              '172.28.48.7': ['Active connections: 673 ', 'server accepts handled requests', ' 3841115 3841115 61362 ',
#                              'Reading: 0 Writing: 1 Waiting: 0 ']}
#             '''
#             for host, value_list in request_content.items():
#                 host_status = {}
#                 host_status["server_ip"] = host
#                 host_status["Active connections"] = value_list[0].strip().split(' ')[-1]
#                 host_status["server accepts"] = value_list[2].strip().split(' ')[0]
#                 host_status["server handled"] = value_list[2].strip().split(' ')[1]
#                 host_status["server requests"] = value_list[2].strip().split(' ')[2]
#                 host_status["Reading"] = value_list[3].strip().split(' ')[1]
#                 host_status["Writing"] = value_list[3].strip().split(' ')[3]
#                 host_status["Waiting"] = value_list[3].strip().split(' ')[5]
#                 self.response.data.append(host_status)
#             self.response.code = 20000
#             self.response.msg = "查询成功"
#             # http_client = AsyncHTTPClient()
#             # import requests
#
#         else:
#             pass
#         self.write(self.response.__dict__)


@router.Route("/nginx/status")
class NginxStatus(BaseHandle):
    # @coroutine
    def post(self, *args, **kwargs):
        # 支持connect|request
        id = self.request_body_data.get("id")[0]
        # id = '(' + ','.join(map(str, id)) + ')'
        action = self.request_body_data.get("action")
        start_time = self.request_body_data.get("start_time", (datetime.datetime.now()+datetime.timedelta(minutes=-30)).strftime("%Y-%m-%d %H:%M:%S"))
        end_time = self.request_body_data.get("end_time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        if action == "connect":
            sql = "select `syn-recv`, `syn-sent`, `last-ack`, `estab`, `closing`, `time-wait`, `close-wait`, `fin-wait-1`, `fin-wait-2`, `update_date` from `conn` where `server_id`='%s' and `update_date` > '%s' and `update_date` < '%s'" %(id ,start_time, end_time)
            # sql = "select * from conn"
        else:
            sql = "select `active`, `reading`, `writing`, `waiting`, `update_date` from `request` where `server_id`='%s' and `update_date` > '%s' and `update_date` < '%s'" % (id, start_time, end_time)
            # sql = "select * from request"

        print(sql)
        try:
            print(sql)
            data_list = self._db.query(sql)
            # data_list = self._db.query("select * from conn")
            # print(data_list)
            full_dict = {}
            for dicts in data_list[0].keys():
                # if dicts in ["id", "server_id"]:
                #     continue
                # temp = {"name": dicts, "data": []}
                # temp = {dicts.replace("-","_"): []}
                full_dict[dicts.replace("-","_")] = []
                for data in data_list:
                    # if (len(str(data[dicts]).split()) > 2 and data[dicts] < start_time) or (len(str(data[dicts]).split()) > 2 and data[dicts] > end_time):
                    #     continue
                    # data = {"": , "", }
                    full_dict[dicts.replace("-", "_")].append(data[dicts])

            self.response.data.append(full_dict)
            self.response.code = 20000
            self.response.msg = "查询成功"
            return self.write(json.dumps(self.response.__dict__, cls=CJsonEncoder))
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "查询失败"
            return self.write(self.response.__dict__)
