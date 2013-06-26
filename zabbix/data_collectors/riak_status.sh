#!/bin/bash
IPADDR="192.168.1.11"
PORT="8098"
curl -s http://$IPADDR:$PORT/stats -H "Accept: text/plain" 2> /dev/null | grep "$1" | awk -F":" '{ print $2 }' | awk -F"," '{print $1}'
