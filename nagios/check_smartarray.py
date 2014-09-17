#!/usr/bin/env python
#
# Check HP SmartArray Status Plugin
# ===
#
# Checks status for all HDDs in all SmartArray controllers.
#
# hpacucli requires root permissions.
#
# Create a file named /etc/sudoers.d/hpacucli with this line inside :
# username ALL=(ALL) NOPASSWD: /usr/sbin/hpacucli
#
# You can get Debian/Ubuntu hpacucli packages here - http://hwraid.le-vert.net/
#
# Copyright 2014 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the MIT license, see LICENSE for details.

import subprocess
import sys
import re
import os


class CheckSmartArrayStatus:
    def __init__(self):
        self.name = 'CheckSmartArrayStatus'
        self.good_disks = []
        self.bad_disks = []
        self.controllers = []
        self.binary = 'hpacucli'
        if os.getuid() != 0:
            self.binary = 'sudo -n -k ' + self.binary

    def execute(self, cmd):
        # returns (rc, stdout, stderr) from shell command
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()
        return (process.returncode, stdout, stderr)

    def ok(self, message):
        print("%s OK: %s" % (self.name, message))
        sys.exit(0)

    def warn(self, message):
        print("%s WARNING: %s" % (self.name, message))
        sys.exit(1)

    def critical(self, message):
        print("%s CRITICAL: %s" % (self.name, message))
        sys.exit(2)

    def unknown(self, message):
        print("%s UNKNOWN: %s" % (self.name, message))
        sys.exit(3)

    def parse_controllers(self, data):
        for line in data.splitlines():
            if line:
                res = re.search(r'Slot\s+([0-9]+)', line)
                if res:
                    self.controllers.append(res.group(1))

    def parse_disks(self, data, controller):
        for line in data.splitlines():
            if line:
                splitted = line.split()
                if re.match(r'^physicaldrive$', splitted[0]):
                    status = splitted[-1]
                    disk = 'ctrl ' + controller + ' ' + line.strip()
                    if status == 'OK':
                        self.good_disks.append(disk)
                    else:
                        self.bad_disks.append(disk)

    def run(self):
        rc, raw_data, err = self.execute(
            "%s ctrl all show status" % self.binary
        )
        if rc != 0:
            error = raw_data + ' ' + err
            self.unknown("hpacucli command failed with %s " % error)
        self.parse_controllers(raw_data)

        for controller in self.controllers:
            rc, raw_data, err = self.execute(
                "%s ctrl slot=%s pd all show status" %
                (self.binary, controller))
            if rc != 0:
                error = raw_data + ' ' + err
                self.unknown("hpacucli command failed with %s " % error)
            self.parse_disks(raw_data, controller)

        if self.bad_disks:
            data = ', '.join(self.bad_disks)
            bad_count = len(self.bad_disks)
            good_count = len(self.good_disks)
            total_count = bad_count + good_count
            self.critical("%s of %s disks are in bad state - %s" %
                          (bad_count, total_count, data))
        else:
            data = len(self.good_disks)
            self.ok("All %s found disks are OK" % data)

if __name__ == "__main__":
    module = CheckSmartArrayStatus()
    module.run()
