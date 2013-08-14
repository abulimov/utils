# !/bin/bash
#
# This script is used to manage backends status in haproxy
# general usage - starting or stoping maintenance
# you need write permissions on haproxy socket
# you need socat to be installed
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com

socket=/var/run/haproxy

command=$1
status()
{
  backend=$1
  server=$2
  if [[ "$server" == "$backend" ]]; then
    server="BACKEND"
  fi
  echo "show stat" | socat unix-connect:$socket stdio | awk -F, '{ printf("%-18s %-12s %s\n",$1,$2,$18) }' | awk "/$backend/ && /$server/ {print \$3}"
}

trigger()
{
  command=$1
  backend=$2
  server=$3
  if [[ "$command" == "disable" ]]; then
    state="UP"
  else
    state="MAINT"
  fi

  if [[ "$server" == "$backend" ]]; then
    server_list=(`echo "show stat" | socat unix-connect:$socket stdio | awk -F, '{ printf("%-18s %-12s %s\n",$1,$2,$18) }' | awk "/$backend/ && !/BACKEND/ && !/no check/ {print \\$2}"`)
  else
    server_list=$server
  fi
  for srv in ${server_list[@]}
  do
    cur_status=$(status $backend $srv)
    while [[ "$cur_status" == "$state" ]]; do
      echo "$command server $backend/$srv"
      #echo "cur_status $cur_status"
      echo "$command server $backend/$srv" | socat unix-connect:$socket stdio
      sleep 1
      cur_status=$(status $backend $srv)
      echo "status changed to $cur_status"
      echo "-----------------------------"
    done
  done
}

case $command in
  stat)
    echo "show stat" | socat unix-connect:$socket stdio | awk -F, '{ printf("%-18s %-12s %s\n",$1,$2,$18) }'
  ;;
  status)
    backend="${2%/*}"
    server="${2##*/}"
    if [ -z "$server" ]; then
      echo "use $0 status backend{/server}"
    else
      status $backend $server
    fi
  ;;
  disable|enable)
    backend="${2%/*}"
    server="${2##*/}"
    if [ -z "$server" ]; then
      echo "use $0 $command backend{/server}"
    else
      trigger $command $backend $server
      trigger $command $backend $server
    fi
  ;;
  *)
    echo "wrong command $command"
    echo "use $0 {stat,status,enable,disable}"
    exit 1
  ;;
esac
