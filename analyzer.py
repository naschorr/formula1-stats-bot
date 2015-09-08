from __future__ import print_function
from collections import OrderedDict
import psycopg2
import json
import sys

## File setup
CREDENTIALS = "credentials.json"
SCHEDULE = "race_schedule.json"

## ToDo : Get rid of global cursor.
## Psycopg2 setup
with open(CREDENTIALS) as credentialsJson:
    credData = json.load(credentialsJson)

try:
    DB = psycopg2.connect(database=credData["database"], host=credData["hostname"],
                  user=credData["username"], password=credData["password"])
    CUR = DB.cursor()
except:
    print("Unable to connect to database")
    print(sys.exc_info()[1])
    sys.exit()


## Desc - Counts the number of rows in the database
## In   - Nothing (cursor defined globally)
## Out  - long int rows
## Mod  - Nothing
## ToDo - Nothing
def countRows():
    CUR.execute("SELECT COUNT(*) FROM f1_bot;")
    return CUR.fetchone()[0]


def sortFlairData(flairs):
    return sorted(flairs.items(), key=lambda x:x[1], reverse=True)


## Size refers to size of dataset the flairs were taken from.
def printFlairData(flairs, requested = [], size = 0):
    size = float(size)

    if not requested:
        for i in flairs:
            for key, value in sorted(i[0].iteritems(), key=lambda i:i[1], reverse=True):
                print("{:<25} {:<5} {:<20} {:<6} %".format(key, value, i[2], round(float(value)/float(i[1])*100, 3)))
            if i[0]:
                print()

    else:
        for i in requested:
            for x in range(len(flairs)):
                if i in flairs[x][0]:
                    print("{:<25} {:<5} {:<20} {:<6} %".format(i, flairs[x][0][i], 
                          flairs[x][2], round(float(flairs[x][0][i])/float(flairs[x][1])*100, 3)))
            print()


def filterFlairs(data, requested):
    output = list(set(requested).intersection(data))
    return dict((x, data[x]) for x in output)


def analyzeRange(start, stop, desiredFlairs = []):
    ## Performs one big database transaction (not meant for large ranges) ymmv
    flairs = {}
    size = 0

    CUR.execute("SELECT time_created, flair FROM f1_bot WHERE time_created BETWEEN %s AND %s;", (start, stop))
    for i in CUR:
        if(i[1] not in flairs):
            flairs[i[1]] = 1
        else:
            flairs[i[1]] = flairs[i[1]] + 1;
        size += 1

    if not desiredFlairs:
        return flairs, size
    else:
        return filterFlairs(flairs, desiredFlairs), size


def analyzeAll(desiredFlairs=[]):
    ## Performs many smaller database transactions
    size = float(countRows())
    chunkSize = 25
    current = 0
    flairs = {}

    while(current * chunkSize < size):
        CUR.execute("SELECT time_created, flair FROM f1_bot ORDER BY post_id LIMIT %s OFFSET %s;", (chunkSize, chunkSize * current))
        print(round(((current * chunkSize)/size)*100, 3), "%")  ## ToDo: Use stdout write buffer instead of spamming lines?
        for i in CUR:
            if(i[1] not in flairs):
                flairs[i[1]] = 1
            else:
                flairs[i[1]] = flairs[i[1]] + 1;
        current += 1;

    if not desiredFlairs:
        return flairs, size
    else:
        return filterFlairs(flairs, desiredFlairs), size


def main(args):

    ## Replace with args
    ## Testing
    flairs = []
    #flairs = ["Sebastian Vettel", "Kimi Rikknen", "Ferrari", "Lewis Hamilton", "Nico Rosberg", "Mercedes"]
    delta = []

    with open(SCHEDULE) as scheduleJson:
        scheduleData = OrderedDict(sorted(json.load(scheduleJson).items(), key=lambda x:x[1]))

    prev_race = 0
    for key, value in scheduleData.iteritems():
        delta.append(analyzeRange(prev_race, value["break"], flairs) + ("pre-" + value["name"],))
        delta.append(analyzeRange(value["break"], value["race"], flairs) + (value["name"],))
        prev_race = value["race"]

    printFlairData(delta, flairs, 0)


main(sys.argv)
