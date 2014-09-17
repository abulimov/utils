#!/usr/bin/env python
#
# Check 3ware Status Plugin
# ===
#
# Checks status for all HDDs in all 3ware controllers.
#
# tw-cli requires root permissions.
#
# Create a file named /etc/sudoers.d/tw-cli with this line inside :
# sensu ALL=(ALL) NOPASSWD: /usr/sbin/tw-cli
#
# You can get Debian/Ubuntu tw-cli packages here - http://hwraid.le-vert.net/
#
# Copyright 2014 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the same terms as Sensu (the MIT license); see LICENSE
# for details.
#
# Inspired by 3ware_status utility

import subprocess
import sys
import re
import os


class Check3wareStatus:
    def __init__(self):
        self.name = 'Check3wareStatus'
        self.good_disks = []
        self.bad_disks = []
        self.controllers = []
        self.binary = 'tw-cli'
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
                controller = line.split()[0]
                if re.match(r'^c[0-9]+$', controller):
                    self.controllers.append(controller)

    def parse_disks(self, data, controller):
        for line in data.splitlines():
            if line:
                splitted = line.split()
                if re.match(r'^[p][0-9]+$', splitted[0]):
                    # '-' means the drive doesn't belong to any array
                    # If is NOT PRESENT too, it means this is an empty port
                    status = splitted[1]
                    name = splitted[0]
                    unit = splitted[2]
                    if not unit == '-' and not unit == 'NOT-PRESENT':
                        line = controller + unit + name + ': ' + status
                        if status == 'OK':
                            self.good_disks.append(line)
                        else:
                            self.bad_disks.append(line)

    def run(self):
        rc, raw_data, err = self.execute("%s info" % self.binary)
        if rc != 0:
            self.unknown("tw-cli command failed with %s " % err)
        self.parse_controllers(raw_data)

        for controller in self.controllers:
            rc, raw_data, err = self.execute("%s info %s" %
                                             (self.binary, controller))
            if rc != 0:
                self.unknown("tw-cli command failed with %s " % err)
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
    module = Check3wareStatus()
    module.run()
