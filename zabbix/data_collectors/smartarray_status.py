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

def parse_disk_status(line):
    splitted = line.split()
    status = splitted[-1]
    return status

def main():
    if len(sys.argv) < 2:
        _fail("usage: %s device_name"%sys.argv[0])

    disk = sys.argv[1]
    m = re.search('^(\d+):([a-zA-Z:0-9]+)$', disk)
    if m is None:
        _fail("device name must be in form C:NN")

    controller = m.group(1)
    physical = m.group(2)

    disks_list = []

    rc, raw_data, err = _run("%s ctrl slot=%s pd %s show status"%(binary_path, controller, physical))
    if rc != 0:
        _fail("hpacucli command failed with %s "%raw_data)
    disk_status = parse_disk_status(raw_data)

    print(disk_status)

if __name__ == "__main__":
    main()
