#!/bin/bash

## Force interactive mode to fg the background jobs
set -m

NAME=rf1-stats-bot
POSTGRES="/usr/sbin/service postgresql status"
POSTGRES_VERSION="9.1"
SLEEP_TIME=5
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"	# http://stackoverflow.com/a/246128
TEMP_DIR=tmp
mkdir -p $TEMP_DIR/
ERR_LOG=$DIR/$TEMP_DIR/err.log
OUT_LOG=$DIR/$TEMP_DIR/out.log
PID_FILE=$DIR/$TEMP_DIR/$NAME.pid

function postgres_started () {
	status="$(eval $POSTGRES)"
	if [ "$(eval grep $POSTGRES_VERSION <<< $status)" ]; then
		return 0
	else
		return 1
	fi
}


function get_pid () {
	# If file exists and has a size > 0
	if [ -s "$PID_FILE" ]; then
		echo "$(eval cat $PID_FILE)"
	else
		return 0
	fi
}

until postgres_started; do
	echo "Postgres not currently running, trying again in $SLEEP_TIME."
	sleep $SLEEP_TIME
done

source $DIR/bin/activate
case "$1" in
	# TODO: background mode?
	-q|--quiet)
		python $DIR/code/scraper.py >/dev/null 2>$ERR_LOG & echo $! > $PID_FILE
		;;

	""|--start)
		echo "Starting $NAME normally (stderr -> stdout and $ERR_LOG)"
		python $DIR/code/scraper.py 2> >(tee $ERR_LOG) & echo $! > $PID_FILE
		;;

	--stop)
		echo "Stopping $NAME"
		pid=$(get_pid)
		if [[ ${pid} -gt 0 ]]; then
			kill $pid
		fi

		## Check if the scraper is really dead
		kill -0 "$pid" > /dev/null 2>&1
		if [[ $? -ne 0 ]]; then
			kill -9 $pid
		else
			exit 0
		fi

		## Final sanity check and exit
		kill -0 "$pid" > /dev/null 2>&1
                if [[ $? -ne 0 ]]; then
                        exit 0
                else
                        exit 1
                fi
		;;

	--pid)
		pid=$(get_pid)
		if [[ ${pid} -gt 0 ]]; then
                        echo "$NAME has PID: $pid"
		else
			echo "$NAME doesn't have a PID"
                fi
		exit 0
		;;

	*)
		echo "Usage: ./rf1-stats-bot [--start | --stop | --pid [-q | --quiet]]"
		exit 1
		;;
esac

# The python scripts are ran in the background so that their pids are easy to get.
# fg just moves them back into the foreground, so that the terminal isn't getting swamped
# by their stdout and stderr.
fg >/dev/null
> $PID_FILE
deactivate

exit 0
