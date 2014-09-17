#!/usr/bin/env python
#
# Control Zabbix Maintenance periods
# ===
#
# Copyright 2014 Alexander Bulimov <lazywolf0@gmail.com>
#
# Released under the MIT license, see LICENSE for details.

"""Zabbix Maintenace.

Usage:
  zabbix_maintenance.py -U=<user> [-P=<password] -S=<server> create \
(<name>) (--hosts|--groups) <targets>...  [--period=<m>] [--no-data] [--force]
  zabbix_maintenance.py -U=<user> [-P=<password] -S=<server> show \
(<name> | --all)
  zabbix_maintenance.py -U=<user> [-P=<password] -S=<server> remove \
(<name> | --all)
  zabbix_maintenance.py (-h | --help)
  zabbix_maintenance.py --version

Options:
  -h --help                  Show this screen.
  --version                  Show version.
  -a --all                   Apply action to all maintenance periods.
  --no-data                  Disable data collection during maintenace period.
  --force                    If maintenance with given name already exists,
                             delete it and create new one.
  --hosts                    Interpret targets as host names.
  --groups                   Interpret targets as group names.
  -P --password=<password>   Login password. If not set, prompt
                             will be displayed.
  -U --user=<user>           Login user.
  -S --server=<server>       Zabbix server uri,
                             for example https://monitor.example.com
  --period=<m>               Period for maintenance window
                             in minutes [default: 10].

"""
import sys
import getpass
import datetime
import time
try:
    from docopt import docopt
except ImportError:
    sys.exit("Missing docopt module (install: pip install docopt)")

try:
    from zabbix_api import ZabbixAPI
except ImportError:
    sys.exit("Missing zabbix-api module (install: pip install zabbix-api)")


def create_maintenance(zbx, group_ids, host_ids, start_time, maintenance_type,
                       period, name, desc):
    end_time = start_time + period
    zbx.maintenance.create(
        {
            "groupids": group_ids,
            "hostids": host_ids,
            "name": name,
            "maintenance_type": maintenance_type,
            "active_since": str(start_time),
            "active_till": str(end_time),
            "description": desc,
            "timeperiods":  [{
                "timeperiod_type": "0",
                "start_date": str(start_time),
                "period": str(period),
            }]
        }
    )


def get_maintenances(zbx, name):
    result = zbx.maintenance.get(
        {
            "output": "extend",
            "filter":
            {
                "name": name
            }
        }
    )

    return result


def parse_maintenances_ids(maintenances):
    maintenance_ids = []
    for res in maintenances:
        maintenance_ids.append(res["maintenanceid"])
    return maintenance_ids


def pretty_maintenance(maint):
    end_time = str(datetime.datetime.fromtimestamp(
        float(maint['active_till'])))
    start_time = str(datetime.datetime.fromtimestamp(
        float(maint['active_since'])))
    if int(maint['maintenance_type']) == 0:
        tp = 'with data collection'
    else:
        tp = 'without data collection'
    pretty = ("%s: since %s, till %s, %s" %
              (maint['name'], start_time, end_time, tp))
    return pretty


def delete_maintenances(zbx, name):
    maintenance = get_maintenances(zbx, name)

    if maintenance:
        ids = parse_maintenances_ids(maintenance)
        zbx.maintenance.delete(ids)


def check_maintenance(zbx, name):
    result = zbx.maintenance.exists(
        {
            "name": name
        }
    )
    return result


def get_group_ids(zbx, host_groups):
    group_ids = []
    for group in host_groups:
        result = zbx.hostgroup.get(
            {
                "output": "extend",
                "filter":
                {
                    "name": group
                }
            }
        )
        if not result:
            return []

        group_ids.append(result[0]["groupid"])

    return group_ids


def get_host_ids(zbx, host_names):
    host_ids = []
    for host in host_names:
        result = zbx.host.get(
            {
                "output": "extend",
                "filter":
                {
                    "name": host
                }
            }
        )
        if not result:
            return []

        host_ids.append(result[0]["hostid"])

    return host_ids


def _fail(msg):
    sys.exit(msg)


def _done(msg):
    print(msg)
    sys.exit(0)


def _ok(msg):
    print(msg)

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Zabbix Maintenance 1.0')

    server_url = arguments['--server']
    login_user = arguments['--user']
    if arguments['--password']:
        login_password = arguments['--password']
    else:
        login_password = getpass.getpass(
            prompt='Enter password for user %s on %s: ' %
                   (login_user, server_url))

    try:
        zbx = ZabbixAPI(server_url)
        zbx.login(login_user, login_password)
    except BaseException as e:
        _fail("Failed to connect to Zabbix server: %s" % e)

    if arguments['--hosts']:
        hosts = arguments['<targets>']
        groups = []
    else:
        hosts = []
        groups = arguments['<targets>']

    name = arguments['<name>']

    if arguments['--no-data']:
        maintenance_type = 1
    else:
        maintenance_type = 0

    if arguments['create']:
        now = datetime.datetime.now()
        start_time = time.mktime(now.timetuple())
        period = 60 * int(arguments['--period'])
        try:
            exists = check_maintenance(zbx, name)
            if exists and not arguments['--force']:
                _fail('Maintenance %s already created, aborting.' % name)
            else:
                if arguments['--force']:
                    delete_maintenances(zbx, name)
                group_ids = get_group_ids(zbx, groups)
                if groups and not group_ids:
                    _fail('One or more group in %s not found, aborting.' %
                          groups)
                host_ids = get_host_ids(zbx, hosts)
                if hosts and not host_ids:
                    _fail('One or more host in %s not found, aborting.' %
                          hosts)
                create_maintenance(zbx, group_ids, host_ids,
                                   start_time, maintenance_type,
                                   period, name, 'desc')
        except BaseException as e:
            _fail(e)
        _done('Done.')

    elif arguments['remove']:
        try:
            exists = check_maintenance(zbx, name)

            if exists:
                if arguments['--all']:
                    name = ''
                delete_maintenances(zbx, name)
                _done('Done.')
            else:
                _done('Nothing to do.')
        except BaseException as e:
            _fail(e)

    elif arguments['show']:
        try:
            if arguments['--all']:
                name = ''
            maintenances = get_maintenances(zbx, name)
            if maintenances:
                for m in maintenances:
                    _ok(pretty_maintenance(m))
            else:
                _done('No maintenances to show.')
        except BaseException as e:
            _fail(e)
