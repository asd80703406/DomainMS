#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 12:20
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: account.py

from config import LDAP_CONFIG
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from passlib.apps import custom_app_context as pwd_context

def generate_auth_token(username, expiration=3600):
    s = Serializer(LDAP_CONFIG["SECRET_KEY"], expires_in=expiration)
    return s.dumps({"username": username}).decode("utf-8")


def verify_auth_token(token):
    s = Serializer(LDAP_CONFIG["SECRET_KEY"])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return False
    except BadSignature:
        return False
    return data["username"]

class Passwd(object):
    def __init__(self, password):
        self.password = password

    def generate_password(self):
        password_hash = pwd_context.encrypt(self.password)
        print(password_hash)
        return password_hash

    def verify_password(self, password_hash):
        return pwd_context.verify(self.password, password_hash)