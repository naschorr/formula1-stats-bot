#!/bin/bash

TEMP_REQS="temp_reqs.txt"

source bin/activate
pip install -r base-requirements.txt
echo "Attempting to pip install psycopg2cffi"
pip install psycopg2cffi
pip freeze > $TEMP_REQS
if ! grep -Fq "psycopg2cffi" $TEMP_REQS
then
	echo "Attempting to install psycopg2 instead"
	pip install psycopg2
fi
rm $TEMP_REQS
exit 1
