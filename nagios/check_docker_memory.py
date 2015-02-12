#!/usr/bin/env python
#
# Check Docker container memory usage Plugin
# ===
#
# Checks Memory Usage status inside given container
# just like check_memory.pl checks it on physical host.
#
# docker requires root permissions.
#
# Create a file named /etc/sudoers.d/docker with this line inside :
# username ALL=(ALL) NOPASSWD: /usr/bin/docker ps*
#
# Copyright 2015 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the MIT license, see LICENSE for details.

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
import subprocess
import sys
import re
import argparse

class CheckDockerMemory:
    """Check memory usage of running docker container"""
    def __init__(self, docker_name, warn, crit, kind):
        self.name = 'CheckDockerMemory'
        self.docker_name = docker_name
        self.warn_level = warn
        self.crit_level = crit
        self.check_kind = kind

        self.binary = 'sudo -n -k docker'

    def execute(self, cmd):
        """Run command in shell"""
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

    def get_docker_id(self, data):
        """Parse data to get matching name and extract id"""
        for line in data.splitlines():
            if line:
                splitted = line.split()
            if re.match(r'^%s$' % self.docker_name, splitted[-1]):
                docker_id = splitted[0]
                return docker_id
        return None


    def run(self):
        """Main class function"""
        rc, raw_data, err = self.execute(
            "%s ps -notrunc" % self.binary
        )
        if rc != 0:
            error = raw_data + ' ' + err
            self.unknown("docker command failed with %s " % error)

        docker_id = self.get_docker_id(raw_data)
        if not docker_id:
            self.critical("No container %s found." % self.docker_name)
        with open('/sys/fs/cgroup/memory/docker/%s/memory.usage_in_bytes' % docker_id) as f:
            mem_used_kb = int(f.read()) / 1024
        with open('/sys/fs/cgroup/memory/docker/%s/memory.limit_in_bytes' % docker_id) as f:
            mem_limit_kb = int(f.read()) / 1024
        with open('/proc/meminfo') as f:
            for line in f.readlines():
                if line and line.startswith('MemTotal'):
                    mem_total_kb = int(line.split()[1])
                    break

        if mem_limit_kb > mem_total_kb:
            mem_limit_kb = mem_total_kb
        mem_free_kb = mem_limit_kb - mem_used_kb

        perfdata = ' | TOTAL=%dKB;;;; USED=%dKB;;;; FREE=%dKB;;;;' % (mem_limit_kb,
                                                                      mem_used_kb,
                                                                      mem_free_kb)
        if self.check_kind == 'used':
            mem_used_percent = mem_used_kb * (100 / mem_limit_kb)
            message = '%5.3f%% (%d kB) used!' % (mem_used_percent, mem_used_kb) + perfdata
            if mem_used_percent > self.crit_level:
                self.critical(message)
            if mem_used_percent > self.warn_level:
                self.warn(message)
            self.ok(message)

        elif self.check_kind == 'free':
            mem_free_percent = mem_free_kb * (100 / mem_limit_kb)
            message = '%5.3f%% (%d kB) free!' % (mem_free_percent, mem_free_kb) + perfdata
            if mem_free_percent < self.crit_level:
                self.critical(message)
            if mem_free_percent < self.warn_level:
                self.warn(message)
            self.ok(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check Docker container memory')
    parser.add_argument('-n', dest='name', required=True, help='Docker container name')
    parser.add_argument('-w', dest='warn', type=int, required=True,
                        help='Percent free/used when to warn')
    parser.add_argument('-c', dest='crit', type=int, required=True,
                        help='Percent free/used when critical')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', dest='kind', action='store_false', help='Check FREE memory')
    group.add_argument('-u', dest='kind', action='store_true', help='Check USED memory')
    args = parser.parse_args()
    if args.kind:
        check_kind = 'used'
    else:
        check_kind = 'free'
    module = CheckDockerMemory(args.name, args.warn, args.crit, check_kind)
    module.run()
