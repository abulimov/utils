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

def parse_disks(data, controller):
    disks = {}
    for line in data.splitlines():
        if line:
            splitted = line.split()
            if re.match(r'^[p][0-9]+$', splitted[0]):
                # '-' means the drive doesn't belong to any array
                # If is NOT PRESENT too, it just means this is an empty port
                if not splitted[2] == '-' and not splitted[1] == 'NOT-PRESENT':
                    disks[controller + splitted[2] + splitted[0]] = splitted[1]
    return disks

def main():
    if len(sys.argv) < 2:
        _fail("usage: %s device_name"%sys.argv[0])

    disk = sys.argv[1]
    m = re.search('^(c\d+)(u\d+)(p\d+)$', disk)
    if m is None:
        _fail("device name must be in form cNuNpN")

    controller = m.group(1)
    unit = m.group(2)
    physical = m.group(3)

    disks_list = []

    rc, raw_data, err = _run("%s info %s"%(binary_path, controller))
    if rc != 0:
        _fail("tw-cli command failed with %s "%err)
    disks_list = parse_disks(raw_data, controller)

    if disk in disks_list:
        print disks_list[disk]
    else:
        _fail("no such disk %s"%disk)

if __name__ == "__main__":
    main()
