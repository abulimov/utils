#!/usr/bin/env python
#
# Check Docker container stats via cAdvisor HTTP API
# ===
#
# Checks CPU or Memory Usage status inside given container
# via cAdvisor API
#
# Copyright 2015 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the MIT license, see LICENSE for details.

from __future__ import unicode_literals
from __future__ import division
from __future__ import print_function
import sys
import argparse
import json
import requests


def get_host_data(cadvisor_url, host_name):
    """Get cAdvisor url, hostname, and return host data in JSON"""
    host_raw_data = requests.get(cadvisor_url + "/api/v1.2/docker/" +
                                 host_name,
                                 timeout=10)
    host_data = json.loads(host_raw_data.text)
    host_id = host_data.keys()[0]
    return host_data[host_id]



def get_host_procs(companion_url, host_id, sort_by):
    """Get cAdvisor url, hostname, and return host data in JSON"""
    payload = {'sort': sort_by, 'limit': 5, 'interval': 30}
    ps_response = requests.get(companion_url + "/api/v1.0" + host_id +
                               "/processes",
                               params=payload,
                               timeout=5)
    ps = json.loads(ps_response.text)
    return ps[-1]["processes"]


def get_machine_data(cadvisor_url):
    """Get cAdvisor url and return parent host data in JSON"""
    response = requests.get(cadvisor_url + "/api/v1.2/machine")
    payload = json.loads(response.text)
    return payload


def ok(message):
    print("CheckDockerStats OK: %s" % message)
    sys.exit(0)


def warn(message):
    print("CheckDockerStats WARNING: %s" % message)
    sys.exit(1)


def critical(message):
    print("CheckDockerStats CRITICAL: %s" % message)
    sys.exit(2)


def unknown(message):
    print("CheckDockerStats UNKNOWN: %s" % message)
    sys.exit(3)


def show_procs(procs, mem_limit):
    """Pretty print host procs in ps-like fashion"""
    mem_limit_kb = mem_limit / 1024
    result = ""
    fmt_line = "%(user)5d %(pid)5d %(cpu)5.1f %(mem)5.1f %(vsz)8d \
                %(rss)8d %(state)6s %(command)s\n"
    if procs:
        result = "\n%5s %5s %5s %5s %8s %8s %6s %s\n" % (
            "USER", "PID", "%CPU", "%MEM", "VSZ", "RSS", "STAT", "COMMAND")
        for proc in procs:
            result += fmt_line % {
                "user": proc["status"]["RealUid"],
                "pid": proc["stat"]["pid"],
                "cpu": proc["relativecpuusage"],
                "mem": proc["status"]["VmRSS"] * 100 / mem_limit_kb,
                "vsz": proc["status"]["VmSize"],
                "rss": proc["status"]["VmRSS"],
                "state": proc["stat"]["state"],
                "command": proc["cmdline"]}
    return result


def calculate_mem_limit(machine_data, host_data):
    """Calculate real memory limit for container"""
    mem_limit = host_data["spec"]["memory"]["limit"]
    mem_limit_host = machine_data["memory_capacity"]

    if mem_limit > mem_limit_host:
        mem_limit = mem_limit_host
    return mem_limit


def process_cpu_checks(machine_data, host_data,
                       warn_level, crit_level, host_procs):
    """Process CPU checks for data"""
    # Usage % = (Used CPU Time (in nanoseconds) for the interval) /
    #   (interval (in nano secs) * num cores)
    mem_limit = calculate_mem_limit(machine_data, host_data)
    cpu_usage_total_per_min = host_data["stats"][-1]["cpu"]["usage"]["total"] -\
        host_data["stats"][0]["cpu"]["usage"]["total"]
    cpu_num_cores = machine_data["num_cores"]
    cpu_usage_percent = cpu_usage_total_per_min / 60 / 10000000 / cpu_num_cores
    perfdata = ' | cpu_usage=%5.2f%%;%d;%d;0;100' % \
        (cpu_usage_percent, warn_level, crit_level)
    message = '%5.2f%% CPU used!' % cpu_usage_percent
    try:
        procs_string = show_procs(host_procs, mem_limit)
    except Exception:
        procs_string = ""

    if cpu_usage_percent > crit_level:
        critical(message + procs_string + perfdata)
    if cpu_usage_percent > warn_level:
        warn(message + procs_string + perfdata)
    ok(message + perfdata)


def process_mem_checks(machine_data, host_data, check_used,
                       warn_level, crit_level, host_procs):
    """Process memory checks for data"""
    mem_limit = calculate_mem_limit(machine_data, host_data)

    mem_used_sum = 0
    for stat in host_data["stats"]:
        mem_used_sum += stat["memory"]["usage"]

    mem_used = mem_used_sum // len(host_data["stats"])
    mem_free_kb = (mem_limit - mem_used) / 1024
    mem_used_kb = mem_used / 1024
    mem_limit_kb = mem_limit / 1024
    mem_used_percent = mem_used * 100 / mem_limit
    mem_free_percent = 100 - mem_used_percent
    perfdata = ' | mem_used=%dKB;%d;%d;0;%d' % (mem_used_kb,
                                                warn_level * mem_limit_kb / 100,
                                                crit_level * mem_limit_kb / 100,
                                                mem_limit_kb)
    try:
        procs_string = show_procs(host_procs, mem_limit)
    except Exception:
        procs_string = ""

    if check_used:
        message = '%5.2f%% Mem (%d kB) used!' % (mem_used_percent, mem_used_kb)
        if mem_used_percent > crit_level:
            critical(message + procs_string + perfdata)
        if mem_used_percent > warn_level:
            warn(message + procs_string + perfdata)
        ok(message + perfdata)
    else:
        message = '%5.2f%% Mem (%d kB) free!' % (mem_free_percent, mem_free_kb)
        if mem_free_percent < args.crit:
            critical(message + procs_string + perfdata)
        if mem_free_percent < args.warn:
            warn(message + procs_string + perfdata)
        ok(message + perfdata)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check Docker container from cAdvisor')
    parser.add_argument('-u', dest='url', required=True,
                        help='cAdvisor url')
    parser.add_argument('-U', dest='companion_url', required=False,
                        help='cAdvisor-companion url')
    parser.add_argument('-n', dest='name', required=True,
                        help='Docker container name')
    parser.add_argument('-w', dest='warn', type=int, required=True,
                        help='Load Average when to warn')
    parser.add_argument('-c', dest='crit', type=int, required=True,
                        help='Load Average when critical')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-C', dest='cpu', action='store_true',
                       help='Check CPU usage percent')
    group.add_argument('-m', dest='mem', action='store_false',
                       help='Check FREE memory percent')
    group.add_argument('-M', dest='mem', action='store_true',
                       help='Check USED memory percent')
    args = parser.parse_args()
    try:
        host_data = get_host_data(args.url, args.name)
        machine_data = get_machine_data(args.url)
    except (requests.exceptions.RequestException, ValueError) as e:
        unknown(e)
    if host_data:
        host_procs = ([], [])
        if args.companion_url:
            try:
                if args.cpu:
                    host_procs = get_host_procs(args.companion_url,
                                                host_data["name"], "cpu")
                else:
                    host_procs = get_host_procs(args.companion_url,
                                                host_data["name"], "mem")
            except (requests.exceptions.RequestException, ValueError) as e:
                print("(can be ignored) Failed to fetch cAdvisor-companion data: %s" % e)
                host_procs = []
        if args.cpu:
            process_cpu_checks(machine_data, host_data,
                               args.warn, args.crit, host_procs)
        else:
            process_mem_checks(machine_data, host_data, args.mem,
                               args.warn, args.crit, host_procs)
    else:
        unknown("Host %s not found" % args.name)
