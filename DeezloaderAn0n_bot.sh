#!/bin/sh

path=`dirname "$0"`
deezbot="${path}/dwsongs-normal.py"

case "$1" in
  start)
    if [ "$(ps aux | grep -c dwsongs-normal.py)" -gt 1 ] 
	then
        echo "DeezloaderAn0n_bot is already running!"
        exit 1
    else
	echo "DeezloaderAn0n_bot started!"
	$deezbot
    fi

    ;;

  stop)
    if [ "$(ps aux | grep -c dwsongs-normal.py)" -gt 1 ]
	then
	pkill -f dwsongs-normal.py
	echo "DeezloaderAn0n_bot stopped!"
    else
	echo "DeezloaderAn0n_bot is not running!"
    	exit 1

    fi

    ;;

  restart)
    $0 stop
    $0 start
    ;;

  *)
    echo "Usage: $0 {start|stop|restart}"
    exit 1
esac

exit 0
