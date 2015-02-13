## Content

This repository contains various SysAdmin-related utils and scripts I've written.

### Nagios-compatible checks

Under **nagios** folder you may find Nagios-compatible check scripts.

Most notable checks are:

* **check_docker_memory.py** - checks used/free memory in running docker container from parent host;
* **check_3ware.py** - checks health status of HDDs attached to 3ware raid controllers;
* **check_smartarray.py** - checks health status of HDDs attached to smartarray raid controllers.

### Zabbix checks and low-level discovery

Under **zabbix** folder you may find Zabbix-related scripts,
mostly for checks and low-level autodiscovery.

### Scripts

Under **scripts** folder you may find various usorted
scripts that might be usefull.

Most notable scripts are:

* **zabbix_maintenance.py** - script to create maintenance periods in Zabbix from CLI;
* **haproxywrap.sh** - lightweight shell wrapper around haproxy control socket;
* **meminfo.py** - small PyQT linux memory viualizer, see [my blog](http://bulimov.ru/it/meminfo-visualizer/) (in Russian).

## License

Released under the [MIT License](http://www.opensource.org/licenses/MIT)
