#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This script is used to get a list of
# disks in 3ware RAID controllers
# to provide Zabbix low-level discovery
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com
# inspired by 3ware_status utility

import subprocess
import sys
import json
import re

binary_path = "/usr/sbin/tw-cli"

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
            splitted = line.split()
            if re.match(r'^c[0-9]+$', splitted[0]):
                controllers.append(splitted[0])
    return controllers

def parse_disks(data, controller):
    disks = []
    for line in data.splitlines():
        if line:
            splitted = line.split()
            if re.match(r'^[p][0-9]+$', splitted[0]):
                # '-' means the drive doesn't belong to any array
                # If is NOT PRESENT too, it just means this is an empty port
                if not splitted[2] == '-' and not splitted[1] == 'NOT-PRESENT':
                    disks.append({
                        '{#3WARE_DISK}': controller + splitted[2] + splitted[0]
                    })
    return disks

def main():
    disks_list = []

    rc, raw_data, err = _run("%s info"%binary_path)
    if rc != 0:
        _fail("tw-cli command failed with %s "%err)
    controllers_list = parse_controllers(raw_data)

    for controller in controllers_list:
        rc, raw_data, err = _run("%s info %s"%(binary_path, controller))
        if rc != 0:
            _fail("tw-cli command failed with %s "%err)
        disks_list.extend(parse_disks(raw_data, controller))

    data = {
        'data': disks_list
    }
    print json.dumps(data)

if __name__ == "__main__":
    main()
