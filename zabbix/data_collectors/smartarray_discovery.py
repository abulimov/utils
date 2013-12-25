#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This script is used to get a list of
# disks in HP SmartArray RAID controllers
# to provide Zabbix low-level discovery
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com
# inspired by 3ware_status utility

import subprocess
import sys
import json
import re

binary_path = "/usr/sbin/hpacucli"

def _run(cmd):
    # returns (rc, stdout, stderr) from shell command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    return (process.returncode, stdout, stderr)

def _fail(msg):
    print(msg)
    sys.exit(1)

def parse_controllers(data):
    controllers = []
    for line in data.splitlines():
        if line:
            res = re.search(r'Slot\s+([0-9]+)', line)
            if res:
                controllers.append(res.group(1))
    return controllers

def parse_disks(data, controller):
    disks = []
    for line in data.splitlines():
        if line:
            splitted = line.split()
            if re.match(r'^physicaldrive$', splitted[0]):
                disks.append({
                    '{#HP_DISK}': controller + ':' + splitted[1]
                })
    return disks

def main():
    disks_list = []

    rc, raw_data, err = _run("%s ctrl all show status"%binary_path)
    if rc != 0:
        _fail("hpacucli command failed with %s "%raw_data)
    controllers_list = parse_controllers(raw_data)

    for controller in controllers_list:
        rc, raw_data, err = _run("%s ctrl slot=%s pd all show status"%(binary_path, controller))
        if rc != 0:
            _fail("hpacucli command failed with %s "%raw_data)
        disks_list.extend(parse_disks(raw_data, controller))

    data = {
        'data': disks_list
    }
    print(json.dumps(data))

if __name__ == "__main__":
    main()
