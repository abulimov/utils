#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys
import json

def _run(cmd):
    # returns (rc, stdout, stderr) from shell command
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()
    return (process.returncode, stdout, stderr)

def parse_vhosts(data):
    vhosts = []
    for line in data.splitlines():
        vhosts.append(line.strip())
    return vhosts

def parse_stat(data, vhost):
    stat = []
    for line in data.splitlines():
        stat.append({
            '{#RABBITMQ_VHOST_NAME}': vhost,
            '{#RABBITMQ_QUEUE_NAME}': line.strip(),
        })
    return stat

def _fail(msg):
    print(msg)
    sys.exit(1)


def main():
    rc, raw_data, err = _run("rabbitmqctl list_vhosts -q")
    if rc != 0:
        _fail("rabbitmqctl command failed with %s "%err)
    vhosts = parse_vhosts(raw_data)

    raw_stats = []
    for vhost_name in vhosts:
        rc, raw_data, err = _run("rabbitmqctl list_queues -p %s -q"%vhost_name)
        if rc != 0:
          _fail("rabbitmqctl command failed with %s "%err)
        raw_stats = raw_stats + parse_stat(raw_data, vhost_name)

    data = {
        'data': raw_stats
    }
    #print json.dumps(data,sort_keys=True, indent=4, separators=(',', ': '))
    print json.dumps(data)

if __name__ == "__main__":
    main()
