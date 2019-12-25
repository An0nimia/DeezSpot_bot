#!/bin/sh
#Path to DeezloaerBot
path="./dwsongs-normal.py"

case "$1" in
  start)
    echo "start"
    if pgrep dwsongs-normal.py > /dev/null
	then
        echo "DeezloaderAn0n_bot is already running!"
        exit 1
    else
	$path
	echo "else"
    fi

    ;;

  stop)
    if pgrep dwsongs-normal.py > /dev/null
	then
		pkill -f dwsongs-normal.py
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
