#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 11:22
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: account.py


import datetime
import json
import traceback
# import ldap3 as ldap
from ldap3 import Server, Connection, ALL
import router
from config import LDAP_CONFIG
from handle.base import BaseHandle, BaseResponse
from libs.account import generate_auth_token, Passwd, verify_auth_token


@router.Route("/user/login")
class UserLogin(BaseHandle):

    def prepare(self):
        self.response = BaseResponse()

    def post(self, *args, **kwargs):
        username = self.request_body_data.get("username", '')
        password = self.request_body_data.get("password", '')
        address = LDAP_CONFIG["LDAP"]
        if username == 'admin':
            u = Passwd(password)
            if u.verify_password(LDAP_CONFIG["password"]):
                token = generate_auth_token(username, expiration=LDAP_CONFIG["EXPIRATION"])
                self.response.code = 20000
                self.response.msg = "认证成功"
                self.response.data.append({"token": token})
            else:
                self.response.code = 50000
                self.response.msg = "认证失败"
            return self.write(self.response.__dict__)

        fullname = username + "@staff.tigerbrokers.com"
        servername = 'ldap://' + address
        s = Server(servername, get_info=ALL)
        c = Connection(s, user=fullname, password=password, receive_timeout=5)
        AUTH_FLAG = True
        try: # 捕获连接LDAP异常
            if c.bind(): # 如果连接LDAP成功并认证通过
                self.response.code = 20000
                self.response.msg = "认证成功"
            else: # 认证失败->密码错误
                self.response.code = 50000
                self.response.msg = "认证失败"
                AUTH_FLAG = False
        except: # 连接LDAP失败
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "认证失败"
            AUTH_FLAG = False
        else: # 表示LDAP认证通过,则开始生成用户token
            if AUTH_FLAG: # LDAP认证成功
                now = datetime.datetime.now()
                currentTime = now.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    token = generate_auth_token(username, expiration=LDAP_CONFIG["EXPIRATION"])
                    sql2 = "SELECT username from user where username = '%s';"
                    user = self._db.get(sql2 % username)
                    print("71:>user: ", user)
                    if user: # 如果有这个用户，则更新token
                        sql3 = "UPDATE user SET `token` = '%s',`login_time` = '%s' where username = '%s';"
                        self._db.update(sql3 % (token, currentTime, username))
                    else:
                        perms = '1,11,11r,12,12r,2,2r,3,31r,32r'
                        sql1 = "INSERT INTO user (`username`,`token`, `perms`, `login_time`) VALUES ('%s', '%s', '%s', '%s');"
                        print(sql1 % (username, token, perms, currentTime))
                        self._db.insert(sql1 % (username, token, perms, currentTime))
                    self.response.data.append({"token": token})
                except:
                    traceback.print_exc()
                    self.response.code = 50000
                    self.response.msg = "后端错误"
        finally:
            c.unbind()
            return self.write(self.response.__dict__)



@router.Route("/user/getPerm")
class UserGetPerm(BaseHandle):
    def get(self, *args, **kwargs):
        page = self.get_argument("page")
        page_size = self.get_argument("pagesize")
        page_start = (int(page) - 1) * int(page_size)
        limitsize = int(page_size)
        sql1 = "select count(*) from user;"
        sql2 = "select username, perms from user limit %d, %d;"
        try:
            # total = self._db.execute_rowcount(sql1)
            # print(total)
            userPerms = self._db.query(sql2 % (page_start, limitsize))
            self.response.code = 20000
            self.response.data = userPerms
            self.response.total = len(userPerms)
            self.response.msg = "查询成功"
            return self.write(self.response.__dict__)
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
            # content = {"code": "50000", "msg": str(e)}
            return self.write(self.response.__dict__)


@router.Route("/user/editPerm")
class UserEditPerm(BaseHandle):
    def post(self, *args, **kwargs):
        sql1 = "UPDATE user set perms = '%s' where username = '%s';"
        username = self.request_body_data.get("username")
        perms = self.request_body_data.get("perms")
        print(username, perms)
        try:
            self._db.update(sql1 %(perms, username))
            self.response.code = 20000
            self.response.msg = "权限修改成功"
        except:
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "权限修改失败"
        return self.write(self.response.__dict__)

@router.Route("/user/token")
class UserToken(BaseHandle):
    def post(self, *args, **kwargs):
        token = self.request.headers.get("X-Token")
        username = verify_auth_token(token)
        if username: # 如果token有效
            sql1 = "SELECT perms from user where username = '%s';"
            perms = self._db.get(sql1 % username)
            self.response.data.append(perms)
            self.response.code = 20000
            self.response.msg = "token验证通过"
        else: # token无效
            self.response.code = 50014
            self.response.msg = "access_token无效或过期"
        return self.write(self.response.__dict__)

@router.Route("/user/logout")
class UserLogout(BaseHandle):
    def get(self, *args, **kwargs):
        print(self.current_user)
        sql = "delete from user where username='%s'"
        try:
            perms = self._db.execute(sql % self.current_user)
            self.response.code = 20000
            self.response.msg = "退出登陆成功"
        except Exception as e: # 删除异常
            traceback.print_exc()
            self.response.code = 50000
            self.response.msg = "后端错误"
        return self.write(self.response.__dict__)