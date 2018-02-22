#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 11:23
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: sslcert.py


import router
import json
import traceback
import subprocess
from libs.utils import CJsonEncoder
from handle.base import BaseHandle
from config import ssl_save_path, ssl_remote_save_path
from tornado.web import RequestHandler
from handle.base import BaseResponse
from backend.ansible_api.playbook import MyPlayBookAPI

@router.Route("/ssl/getAll")
class SSLGetAll(BaseHandle):
    def get(self, *args, **kwargs):
        page = self.get_argument("page")
        page_size = self.get_argument("pagesize")
        page_start = (int(page) - 1) * int(page_size)
        limitsize = int(page_size)
        sql2 = "select id, domainname, filename, filepath, start_time, end_time, invalid_time from sslinfo limit %d, %d;"
        try:
            result = self._db.query(sql2 % (page_start, limitsize))
            self.response.code = 20000
            self.response.data = result
            self.response.msg = "查询成功"
            self.response.total = len(result)
        except Exception as e:
            print(e)
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(json.dumps(self.response.__dict__, cls=CJsonEncoder))


@router.Route("/ssl/add")
class SSLAdd(BaseHandle):
    def post(self, *args, **kwargs):
        file_metas = self.request.files["file"][0]  # 获取上传文件信息
        file_name = file_metas['filename']  # 获取文件的名称
        print("filename:", file_name)
        if not file_name.endswith(".pem"):
            print("not equal pem")
            self.response.code = 50000
            self.response.msg = "文件格式错误"
            print(self.response.__dict__)
            return self.write(self.response.__dict__)
        from datetime import datetime
        from OpenSSL import crypto as c

        cert = c.load_certificate(c.FILETYPE_PEM, file_metas["body"])
        start_time = datetime.strptime(cert.get_notBefore().decode(), "%Y%m%d%H%M%SZ").strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(cert.get_notAfter().decode(), "%Y%m%d%H%M%SZ").strftime('%Y-%m-%d %H:%M:%S')
        invalid_time = (datetime.strptime(cert.get_notAfter().decode(), "%Y%m%d%H%M%SZ") - datetime.now()).days
        if invalid_time <= 0:
            self.response.msg = "证书已过期,请重新上传"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        try:
            import os  # 引入os路径处理模块
            if os.path.exists(os.path.join(ssl_save_path, file_name)):  # pem文件已存在
                import time
                nowtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
                print('Now: ',nowtime)
                print(os.path.join(ssl_save_path, file_name))
                os.rename(os.path.join(ssl_save_path, file_name),
                          os.path.join(ssl_save_path, file_name) + "-%s" % nowtime)
            with open(os.path.join(ssl_save_path, file_name), 'wb') as up:  # os拼接文件保存路径，以字节码模式打开
                # print(type(file_metas['body']))
                up.write(file_metas['body'])  # 将文件写入到保存路径目录
            filepath = os.path.join(ssl_save_path, file_name)
            domain_name = file_name[0:-4]

            insert_sql = "insert into sslinfo (`domainname`,`filename`,`filepath`,`start_time`,`end_time`,`invalid_time`,`last_editor`) " \
                         "VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s' )" % (
                             domain_name, file_name, ssl_remote_save_path, start_time, end_time, invalid_time, self.current_user)
            select_sql = "select domainname from sslinfo where domainname='%s'" % domain_name
            update_sql = "update sslinfo set `start_time`='%s',`end_time`='%s',`invalid_time`=%s, `last_editor`='%s'" \
                         "where domainname='%s'" % (start_time, end_time, invalid_time, self.current_user, domain_name)
            if self._db.execute_rowcount(select_sql): # 记录已存在
                self._db.execute(update_sql)
            else:
                self._db.insert(insert_sql)

            self.response.msg = "上传成功"
            self.response.code = 20000
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = '后端错误'
        return self.write(self.response.__dict__)

@router.Route("/ssl/delete")
class SSLDelete(BaseHandle):
    def post(self, *args, **kwargs):
        id = self.request_body_data["id"]
        id = '(' + ','.join(map(str, id)) + ')'
        # id = self.get_argument("id")
        sql = "delete from sslinfo where id in %s;"
        try:
            self._db.execute(sql % id)
            self.response.code = 20000
            self.response.msg = "删除成功"
        except Exception as e:
            print(e)
            self.response.code = 50000
            self.response.msg = "后端错误"

        return self.write(self.response.__dict__)

@router.Route("/ssl/up")
class SSLUp(RequestHandler):
    def get(self, *args, **kwargs):
        return self.render("index.html")

    def post(self, *args, **kwargs):
        from libs.database import db
        self._db = db()
        self.response = BaseResponse()
        file_metas = self.request.files["file"][0]  # 获取上传文件信息
        file_name = file_metas['filename']  # 获取文件的名称
        print("filename:", file_name)
        if not file_name.endswith(".pem"):
            print("not equal pem")
            self.response.code = 50000
            self.response.msg = "文件格式错误"
            print(self.response.__dict__)
            return self.write(self.response.__dict__)
        from datetime import datetime
        from OpenSSL import crypto as c

        cert = c.load_certificate(c.FILETYPE_PEM, file_metas["body"])
        start_time = datetime.strptime(cert.get_notBefore().decode(), "%Y%m%d%H%M%SZ").strftime('%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(cert.get_notAfter().decode(), "%Y%m%d%H%M%SZ").strftime('%Y-%m-%d %H:%M:%S')
        invalid_time = (datetime.strptime(cert.get_notAfter().decode(), "%Y%m%d%H%M%SZ") - datetime.now()).days
        if invalid_time <= 0:
            self.response.msg = "证书已过期,请重新上传"
            self.response.code = 50000
            return self.write(self.response.__dict__)
        try:
            import os  # 引入os路径处理模块
            if os.path.exists(os.path.join(ssl_save_path, file_name)):  # pem文件已存在
                import time
                nowtime = time.strftime("%Y%m%d%H%M%S", time.localtime())
                print(os.path.join(ssl_save_path, file_name))
                os.rename(os.path.join(ssl_save_path, file_name),
                          os.path.join(ssl_save_path, file_name) + "-%s" % nowtime)
            with open(os.path.join(ssl_save_path, file_name), 'wb') as up:  # os拼接文件保存路径，以字节码模式打开
                # print(type(file_metas['body']))
                up.write(file_metas['body'])  # 将文件写入到保存路径目录
            filepath = os.path.join(ssl_save_path, file_name)
            domain_name = file_name[0:-4]

            insert_sql = "insert into sslinfo (`domainname`,`filename`,`filepath`,`start_time`,`end_time`,`invalid_time`,`last_editor`) " \
                         "VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s' )" % (
                         domain_name, file_name, filepath, start_time, end_time, invalid_time, self.current_user)
            select_sql = "select domainname from sslinfo where domainname='%s'" % domain_name
            update_sql = "update sslinfo set `start_time`='%s',`end_time`='%s',`invalid_time`=%s, `last_editor`='%s'" \
                         "where domainname='%s'" % (start_time, end_time, invalid_time, self.current_user, domain_name)
            if self._db.execute_rowcount(select_sql):  # 记录已存在
                print(update_sql)
                self._db.execute(update_sql)
            else:
                print(insert_sql)
                self._db.insert(insert_sql)

            self.response.msg = "上传成功"
            self.response.code = 20000
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = '后端错误'
        return self.write(self.response.__dict__)

@router.Route("/ssl/transfer")
class SSLTransfer(BaseHandle):
    def post(self, *args, **kwargs):
        push_type = self.request_body_data["type"]
        localfile = self.request_body_data["filepath"]
        try:
            # id = '(' + ','.join(map(str, id)) + ')'
            if push_type == "all":
                sql = "select ip2 from nginx;"
            else:
                sql = "select ip2 from nginx where server_type='%s';" % push_type

            host_list = []
            ips = self._db.query(sql)
            [host_list.append(x["ip2"]) for x in ips]
            ext_vars = {"host_list": host_list, "src": localfile, "dest": "/tmp"}
            print(host_list)
            # from backend.justtest import myplaybook
            ssl_job = MyPlayBookAPI(playbooks='backend/playbook_jobs/scp_sslcert_to_remote.yml',
                                        ssh_user='lhop',
                                        project_name="test",
                                        forks=len(host_list), ext_vars=ext_vars)
            ssl_job.run()
            result = ssl_job.get_result()
            print(result)
            success_hosts = list(result["success"].keys())
            failed_hosts = list(result["failed"].keys())
            unreachable_hosts = list(result["unreachable"].keys())
            info = {
                "success": success_hosts,
                "failed": failed_hosts,
                "unreachable": unreachable_hosts
            }
            print(info)
            self.response.msg = "任务完成"
            self.response.code = 20000
            self.response.data.append(info)
        except:
            traceback.print_exc()
            self.response.msg = "后端错误"
            self.response.code = 50000
        return self.write(json.dumps(self.response.__dict__))