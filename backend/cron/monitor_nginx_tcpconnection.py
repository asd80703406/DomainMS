#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/3 16:51
# @Author  : wangzhigang@tigerbrokers.com
# @FileName: monitor_nginx_tcpconnection.py

from libs.database import db
from backend.ansible_api.playbook import MyPlayBookAPI
# python3 -m backend.cron.monitor_nginx_tcpconnection
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
    job = MyPlayBookAPI(playbooks='backend/playbook_jobs/get_remote_tcpconnection.yml',
                        ssh_user='lhop',
                        ext_vars=ext_vars, forks=5)
    job.run()
    request_content = job.get_result()
    end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:00")
    for host, value in request_content["success"].items():
        host_id = ip_id_dict[host]
        stdout = value["stdout_lines"]
        # end_time = value["end"][:19]
        # 'stdout_lines': ['LAST-ACK 50', 'SYN-RECV 16', 'ESTAB 5627', 'FIN-WAIT-1 172', 'CLOSING 9', 'FIN-WAIT-2 1639', 'TIME-WAIT 18212', 'LISTEN 7']
        tcp_dict = {}
        for item in stdout:
            tcp_dict[item.split()[0]] = item.split()[1]
        sql = "insert into conn (`server_id`,   `syn-recv`, `syn-sent`, `last-ack`, `estab`, `closing`, `time-wait`, `close-wait`, `fin-wait-1`, `fin-wait-2`, `update_date` ) " \
              "values (%d, %s, %s, %s, %s, %s, %s, %s, %s, %s, '%s' )" % (host_id, tcp_dict.get("SYN-RECV", 0), tcp_dict.get("SYN-SENT", 0),
                                                                          tcp_dict.get("LAST-ACK", 0), tcp_dict.get("ESTAB", 0), tcp_dict.get("CLOSING", 0),
                                                                          tcp_dict.get("TIME-WAIT", 0), tcp_dict.get("CLOSE-WAIT", 0), tcp_dict.get("FIN-WAIT-1", 0),
                                                                          tcp_dict.get("FIN-WAIT-2", 0), end_time)
        db_handle.insert(sql)

    db_handle.close()

if __name__ == "__main__":
    main()

