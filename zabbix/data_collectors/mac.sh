#!/bin/bash
# License: MIT
# Author: Alexander Bulimov, lazywolf0@gmail.com

if [ -z "$1" ]; then
    echo "no args specified, exiting!"
    exit 1 
fi
#don't forget that Zabbix don't set $PATH when running scripts
filename=/usr/share/zabbix/scripts/oui.txt
tmpfile=/tmp/oui.txt
link=http://standards.ieee.org/develop/regauth/oui/oui.txt
sed=/bin/sed
awk=/usr/bin/awk

case $1 in
    -s)
        silent=1
        mac=$2
        if [ -z "$2" ]; then
            echo "no mac specified, exiting!"
            exit 1
        fi
        ;;
    -u)
        wget $link -O $tmpfile
        if [ $? -gt 0 ]; then 
            echo "download error, exiting"
            exit 1
        else 
            echo "Download ok!"
            echo "Moving $tmpfile to $filename..."
            mv -f $tmpfile $filename
            if [ $? -gt 0 ]; then
                echo "Error!"
            else
                echo "Success!"
            fi
            exit 0
        fi
        ;;
    *)    
        mac=$1
        ;;
    esac
if [ ! -f $filename ]; then 
    if [ -z $silent ]; then
        echo "no mac list file, dowload it? [y/n]"
    else
        exit 1
    fi
    while :
    do 
        read INPUT_STRING
        case $INPUT_STRING in
        y)
            echo "Trying to download from $link"
            wget $link
            if [ $? -gt 0 ]; then 
                echo "download error, exiting"
                exit 1
            else 
                echo "Download ok!"
            fi
            break
            ;;
        n)
            echo "exiting!"
            exit 0
            ;;
        *)
            echo "wrong input, use [y/n]"
            ;;
        esac
    done
fi
if [ ${#mac} -lt 8 ]; then
    mac=`echo "$mac" | $sed 's/^\(..\)\(..\)\(..\)/\1-\2-\3/' `
else
    mac=`echo "$mac" | $sed -e 's/:/-/g'`
fi
mac=${mac:0:8}
if [ -z $silent ]; then
    echo "Searching for $mac..."
fi
result=`$awk --assign IGNORECASE=1 '/hex/ && /'$mac'/ {for (x=3; x<=NF; x++) {printf("%s ",$x)}}' $filename`
if [ -z "$result" ]; then
    result="no info"
fi
echo -n $result
