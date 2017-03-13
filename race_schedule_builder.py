from collections import OrderedDict
import json
import sys
import time

# Globals
RACE = "race"
RECESS = "break"
EVENT_LEN = 3

## JSON files
SCHEDULE = "race_schedule.json"


def printEventData(event):
    print event["name"]
    print "End of race weekend on", event[RACE],
    print time.strftime('%m-%d-%Y %H:%M:%S', time.gmtime(event[RACE]))
    print "End of previous break on", event[RECESS], 
    print time.strftime('%m-%d-%Y %H:%M:%S', time.gmtime(event[RECESS])), "\n"

def main(args):
    with open(SCHEDULE) as scheduleJson:
        scheduleData = OrderedDict(sorted(json.load(scheduleJson).items(), key=lambda x:x[1]))

    for key, value in scheduleData.iteritems():
        race = value[RACE]
        recess = race - (EVENT_LEN * 24 * 60 * 60) + 1
        value[RECESS] = recess

        printEventData(value)

    with open(SCHEDULE, 'w') as output:
       json.dump(scheduleData, output)


main(sys.argv)