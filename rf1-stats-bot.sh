#!/bin/bash

## Force interactive mode to fg the background jobs
set -m

NAME=rf1-stats-bot
POSTGRES="/usr/sbin/service postgresql status"
POSTGRES_VERSION="9.1"
SLEEP_TIME=5
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"	# http://stackoverflow.com/a/246128
mkdir -p tmp/
ERR_LOG=$DIR/tmp/err.log
OUT_LOG=$DIR/tmp/out.log
PID_FILE=$DIR/tmp/$NAME.pid

function postgres_started {
	status="$(eval $POSTGRES)"
	if [ "$(eval grep $POSTGRES_VERSION <<< $status)" ]; then
		return 0
	else
		return 1
	fi
}

until postgres_started; do
	echo "Postgres not currently running, trying again in $SLEEP_TIME."
	sleep $SLEEP_TIME
done

source $DIR/bin/activate
case "$1" in
	# TODO: background mode?
	--quiet|-q)
		python $DIR/code/scraper.py >/dev/null 2>$ERR_LOG & echo $! > $PID_FILE
		;;
	*)
		echo "Starting $NAME normally (stderr -> stdout and $ERR_LOG)"
		python $DIR/code/scraper.py 2> >(tee $ERR_LOG) & echo $! > $PID_FILE
		;;
esac
# The python scripts are ran in the background so that their pids are easy to get.
# fg just moves them back into the foreground, so that the terminal isn't getting swamped
# by their stdout and stderr.
fg >/dev/null
> $PID_FILE
deactivate
