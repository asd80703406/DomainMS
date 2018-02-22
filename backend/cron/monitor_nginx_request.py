#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/3 16:51
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: monitor_nginx_request.py

from libs.database import db
from backend.ansible_api.playbook import MyPlayBookAPI
import datetime
def main():

    db_handle = db()
    hostsinfo = db_handle.query("select server_id,ip2 from nginx;")
    host_list = []
    ip_id_dict = {}
    for hostinfo in hostsinfo:
        ip_id_dict[hostinfo["ip2"]] = hostinfo["server_id"]
        host_list.append(hostinfo["ip2"])
    ext_vars = {"host_list": host_list}
    job = MyPlayBookAPI(playbooks='backend/playbook_jobs/get_nginx_request_status.yml',
                        ssh_user='lhop',
                        ext_vars=ext_vars, forks=5)
    job.run()
    request_content = job.get_result()
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    for host, value in request_content["success"].items():
        host_id = ip_id_dict[host]
        stdout = value["stdout_lines"]
        # end_time = value["end"][:19]
        # 'stdout_lines': ['Active connections: 3896 ', 'server accepts handled requests', ' 1182015493 1182015493 5390597523 ', 'Reading: 1 Writing: 16 Waiting: 3221 ']
        request_dict = {}
        request_dict["active"] = stdout[0].strip().split()[2]
        request_dict["reading"] = stdout[3].strip().split()[1]
        request_dict["writing"] = stdout[3].strip().split()[3]
        request_dict["waiting"] = stdout[3].strip().split()[5]
        sql = "insert into request (`server_id`,   `active`, `reading`, `writing`, `waiting`,`update_date`) " \
              "values (%d, %s, %s, %s, %s, '%s')" % (host_id, request_dict.get("active", 0), request_dict.get("reading", 0),
                                                 request_dict.get("writing", 0), request_dict.get("waiting", 0), end_time)

        db_handle.insert(sql)

    db_handle.close()

if __name__ == "__main__":
    main()

