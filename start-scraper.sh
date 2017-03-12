#!/bin/bash

POSTGRES="/usr/sbin/service postgresql status"
POSTGRES_VERSION="9.1"

function postgres_started {
	status="$(eval $POSTGRES)"
	if [ "$(eval grep $POSTGRES_VERSION <<< $status)" ]; then
		return 0
	else
		return 1
	fi
}

SLEEP_TIME=5

until postgres_started; do
	echo "$(POSTGRES_STATUS)"
	echo "Postgres not currently running, trying again in $SLEEP_TIME."
	sleep $SLEEP_TIME
done

# http://stackoverflow.com/a/246128
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

source $DIR/bin/activate
python $DIR/code/scraper.py
deactivate
