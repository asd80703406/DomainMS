/*
Navicat MySQL Data Transfer

Source Server         : domainMS
Source Server Version : 50704
Source Host           : 
Source Database       : nginx

Target Server Type    : MYSQL
Target Server Version : 50704
File Encoding         : 65001

Date: 2018-02-22 11:30:43
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for `conf`
-- ----------------------------
DROP TABLE IF EXISTS `conf`;
CREATE TABLE `conf` (
  `conf_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `domain_id` int(11) DEFAULT NULL COMMENT 'domains表中的domain_id',
  `server_id` int(11) DEFAULT NULL COMMENT 'nginx表中的server_id',
  `filename` varchar(16) NOT NULL DEFAULT '' COMMENT '域名配置文件名',
  `filepath` varchar(64) NOT NULL DEFAULT '' COMMENT '域名配置文件路径',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`conf_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='conf表';

-- ----------------------------
-- Records of conf
-- ----------------------------

-- ----------------------------
-- Table structure for `conn`
-- ----------------------------
DROP TABLE IF EXISTS `conn`;
CREATE TABLE `conn` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `server_id` int(11) DEFAULT NULL COMMENT 'server表中对应的server_id',
  `SYN-RECV` int(11) NOT NULL DEFAULT '0' COMMENT 'SYN-RECV连接数量',
  `SYN-SENT` int(11) NOT NULL DEFAULT '0' COMMENT 'SYN-SENT连接数量',
  `LAST-ACK` int(11) NOT NULL DEFAULT '0' COMMENT 'LAST-ACK连接数量',
  `ESTAB` int(11) NOT NULL DEFAULT '0' COMMENT 'ESTAB连接数量',
  `CLOSING` int(11) NOT NULL DEFAULT '0' COMMENT 'CLOSING连接数量',
  `TIME-WAIT` int(11) NOT NULL DEFAULT '0' COMMENT 'TIME-WAIT连接数量',
  `CLOSE-WAIT` int(11) NOT NULL DEFAULT '0' COMMENT 'CLOSE-WAIT连接数量',
  `FIN-WAIT-1` int(11) NOT NULL DEFAULT '0' COMMENT 'FIN-WAIT-1连接数量',
  `FIN-WAIT-2` int(11) NOT NULL DEFAULT '0' COMMENT 'FIN-WAIT-2连接数量',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Nginx connection 表';

-- ----------------------------
-- Records of conn
-- ----------------------------

-- ----------------------------
-- Table structure for `domains`
-- ----------------------------
DROP TABLE IF EXISTS `domains`;
CREATE TABLE `domains` (
  `domain_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `domain_name` varchar(64) NOT NULL DEFAULT '' COMMENT '域名',
  `region` enum('国内','国外') NOT NULL DEFAULT '国内' COMMENT '域名提供给国内还是国外',
  `domain_type` enum('线上','测试') NOT NULL DEFAULT '线上' COMMENT '域名是线上还是测试',
  `line1` int(11) NOT NULL COMMENT 'IDC代理线路1',
  `line2` int(11) DEFAULT NULL COMMENT 'IDC代理线路2',
  `line3` int(11) DEFAULT NULL COMMENT 'IDC代理线路3',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`domain_id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 COMMENT='domains表';

-- ----------------------------
-- Records of domains
-- ----------------------------


-- ----------------------------
-- Table structure for `lines`
-- ----------------------------
DROP TABLE IF EXISTS `lines`;
CREATE TABLE `lines` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `line` varchar(64) NOT NULL DEFAULT '' COMMENT 'IDC代理线路',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8 COMMENT='lines表';

-- ----------------------------
-- Records of lines
-- ----------------------------
INSERT INTO `lines` VALUES ('1', '世纪互联', '2018-01-04 18:23:49', '');
INSERT INTO `lines` VALUES ('2', '将军澳机房', '2018-01-04 18:23:57', '');
INSERT INTO `lines` VALUES ('3', '荃湾机房', '2018-01-04 18:24:04', '');
INSERT INTO `lines` VALUES ('4', '广州机房', '2018-01-04 18:24:08', '');
INSERT INTO `lines` VALUES ('5', '深圳机房', '2018-01-04 18:24:12', '');
INSERT INTO `lines` VALUES ('6', '', '2018-01-29 16:03:42', '');

-- ----------------------------
-- Table structure for `nginx`
-- ----------------------------
DROP TABLE IF EXISTS `nginx`;
CREATE TABLE `nginx` (
  `server_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `group_id` int(11) DEFAULT NULL COMMENT 'Nginx group id',
  `lhzq_sn` varchar(16) NOT NULL DEFAULT '' COMMENT '老虎资产编号',
  `idc` varchar(16) NOT NULL DEFAULT '' COMMENT '机房',
  `ip1` varchar(16) NOT NULL DEFAULT '0.0.0.0' COMMENT '外网ip地址',
  `ip2` varchar(16) NOT NULL DEFAULT '0.0.0.0' COMMENT '内网ip地址',
  `vip` varchar(16) NOT NULL DEFAULT '0.0.0.0' COMMENT '虚拟IP地址',
  `role` varchar(16) NOT NULL DEFAULT 'slave' COMMENT 'Nginx主备状态',
  `server_type` enum('线上','测试') DEFAULT '线上' COMMENT '服务器是线上还是测试',
  `create_date` timestamp NOT NULL DEFAULT '2015-01-01 00:00:00' COMMENT '创建时间',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`server_id`),
  UNIQUE KEY `ip1` (`ip1`),
  UNIQUE KEY `ip2` (`ip2`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8 COMMENT='Nginx表';

-- ----------------------------
-- Records of nginx
-- ----------------------------


-- ----------------------------
-- Table structure for `request`
-- ----------------------------
DROP TABLE IF EXISTS `request`;
CREATE TABLE `request` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `server_id` int(11) DEFAULT NULL COMMENT 'server表中对应的server_id',
  `active` int(11) NOT NULL DEFAULT '0' COMMENT 'active连接数量',
  `reading` int(11) NOT NULL DEFAULT '0' COMMENT 'reading连接数量',
  `writing` int(11) NOT NULL DEFAULT '0' COMMENT 'writing连接数量',
  `waiting` int(11) NOT NULL DEFAULT '0' COMMENT 'waiting连接数量',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='Nginx request表';

-- ----------------------------
-- Records of request
-- ----------------------------

-- ----------------------------
-- Table structure for `sslinfo`
-- ----------------------------
DROP TABLE IF EXISTS `sslinfo`;
CREATE TABLE `sslinfo` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `domainname` varchar(32) NOT NULL,
  `filename` varchar(128) NOT NULL DEFAULT '' COMMENT '证书文件名',
  `filepath` varchar(64) NOT NULL DEFAULT '/usr/local/nginx/conf/ssl/' COMMENT '证书存放路径',
  `start_time` timestamp NOT NULL DEFAULT '2015-01-01 00:00:00' COMMENT '证书生效时间',
  `end_time` timestamp NOT NULL DEFAULT '2015-01-01 00:00:00' COMMENT '证书失效时间',
  `invalid_time` int(11) DEFAULT '0' COMMENT '证书失效倒计时',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8 COMMENT='SSL表';

-- ----------------------------
-- Records of sslinfo
-- ----------------------------

-- ----------------------------
-- Table structure for `transfer_log`
-- ----------------------------
DROP TABLE IF EXISTS `transfer_log`;
CREATE TABLE `transfer_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT 'task_id',
  `success_host` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `success_detail` text COLLATE utf8mb4_unicode_ci,
  `failed_host` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `failed_detail` text COLLATE utf8mb4_unicode_ci,
  `unreachable` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `unreachable_detail` text COLLATE utf8mb4_unicode_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of transfer_log
-- ----------------------------

-- ----------------------------
-- Table structure for `upstream_server`
-- ----------------------------
DROP TABLE IF EXISTS `upstream_server`;
CREATE TABLE `upstream_server` (
  `upstream_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `domain_id` int(11) DEFAULT NULL COMMENT '域名domain_id',
  `lhzq_sn` varchar(16) DEFAULT '' COMMENT '老虎资产编号',
  `idc` varchar(16) DEFAULT '' COMMENT '机房',
  `ip1` varchar(16) NOT NULL DEFAULT '0.0.0.0' COMMENT '外网ip地址',
  `ip2` varchar(16) NOT NULL DEFAULT '0.0.0.0' COMMENT '内网ip地址',
  `port` int(11) DEFAULT NULL COMMENT '端口号',
  `function` varchar(16) NOT NULL DEFAULT 'rr' COMMENT 'upstream调度算法',
  `weight` varchar(16) NOT NULL DEFAULT '1' COMMENT 'upstream调度算法',
  `max_fails` int(11) NOT NULL DEFAULT '1' COMMENT 'max_fails最大次数',
  `fail_timeout` varchar(16) NOT NULL DEFAULT '10s' COMMENT 'fail_timeout超时时间',
  `update_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '修改时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`upstream_id`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8 COMMENT='Nginx Server表';

-- ----------------------------
-- Records of upstream_server
-- ----------------------------


-- ----------------------------
-- Table structure for `user`
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增id',
  `username` varchar(64) DEFAULT NULL COMMENT '用户名',
  `token` varchar(512) DEFAULT NULL COMMENT '用户token信息',
  `perms` varchar(512) DEFAULT NULL COMMENT '用户权限',
  `login_time` timestamp NOT NULL DEFAULT '2015-01-01 00:00:00' COMMENT '用户登入时间',
  `logout_time` timestamp NOT NULL DEFAULT '2015-01-01 00:00:00' COMMENT '用户登出时间',
  `last_editor` varchar(16) NOT NULL DEFAULT '' COMMENT '最后修改人',
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8 COMMENT='USER表';

-- ----------------------------
-- Records of user
-- ----------------------------

