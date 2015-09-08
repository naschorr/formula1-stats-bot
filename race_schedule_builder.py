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
        scheduleData = json.load(scheduleJson)
    print scheduleData

    for i in range(1, len(scheduleData)+1):  ## Fix
        index = str(i)
        race = scheduleData[index][RACE]
        recess = race - (EVENT_LEN * 24 * 60 * 60) + 1
        scheduleData[index][RECESS] = recess

        printEventData(scheduleData[index])

    with open(SCHEDULE, 'w') as output:
       json.dump(scheduleData, output)


main(sys.argv)