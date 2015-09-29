from __future__ import print_function
from collections import OrderedDict
import psycopg2
import json
import sys
import time

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


def sortFlairs(flairs):
    return sorted(flairs.items(), key=lambda x:x[1], reverse=True)


## Gets the size of a given set of flairs.
def getSize(flairs):
    size = 0
    for key, value in flairs.iteritems():
        size += value
    return size


## Outputs the flair, the number of flairs, and the relative frequency of that flair to the terminal.
def printFlairFreq(flairs):
    size = float(getSize(flairs))

    for i in sortFlairs(flairs):
        print("{:<25} {:<7} {:<6} %".format(i[0], i[1], round(i[1]/size*100, 3)))


## Builds/updates a dict based on the values provided by the input list. Acts as a tally
def appendListToDict(dictOut, listIn):
        for i in listIn:
            this = i[0]
            if(this not in dictOut):
                dictOut[this] = 1
            else:
                dictOut[this] += 1
        return dictOut


## Grabs all flairs from db within given range, and puts them in a dict that corresponds to how many
##  instances of that flair there are. Performs one big database transaction (not meant for large ranges)
def getRange(start, stop, filterFlairs = []):
    if(not filterFlairs):
        CUR.execute("SELECT flair FROM f1_bot WHERE time_created BETWEEN %s and %s;", (start, stop))
    else:
        CUR.execute("SELECT flair FROM f1_bot WHERE time_created BETWEEN %s and %s AND flair IN %s;", 
                    (start, stop, tuple(filterFlairs)))

    output = {}
    return appendListToDict(output, CUR)


## Grabs all flairs in the db, and puts them in a dict that corresponds to how many instances of 
##  that flair there are. Performs many smaller database transactions
def getAll(filterFlairs = []):
    size = float(countRows())
    chunkSize = 25
    current = 0
    output = {}

    if(not filterFlairs):
        while(current * chunkSize < size):
            CUR.execute("SELECT flair FROM f1_bot LIMIT %s OFFSET %s;", (current, current + chunkSize))
            output = appendListToDict(output, CUR)
            current += chunkSize
    else:
        while(current * chunkSize < size):
            CUR.execute("SELECT flair FROM f1_bot WHERE flair IN %s LIMIT %s OFFSET %s;", 
                        (tuple(filterFlairs), current, current + chunkSize))
            output = appendListToDict(output, CUR)
            current += chunkSize

    return output


def main(args):

    ## Replace with args
    ## Testing
    flairs = []
    flairs = ["Sebastian Vettel", "Kimi Rikknen", "Ferrari", "Lewis Hamilton", "Nico Rosberg", "Mercedes"]

    with open(SCHEDULE) as scheduleJson:
        ## Replace with modified sortFlairs?
        scheduleData = OrderedDict(sorted(json.load(scheduleJson).items(), key=lambda x:x[1]))

    ## Put this in its own function
    prevRace = 0
    counter = 1
    seasonLength = len(scheduleData)
    while(counter <= seasonLength):
        value = scheduleData[str(counter)]
        currTime = time.time()
        prerace = value["break"]
        race = value["race"]
        if(prerace <= currTime or prevRace <= currTime):
            print("PRE-" + value["name"].upper())
            printFlairFreq(getRange(prevRace, prerace, flairs))
            print()
        else:
            break
        if(race <= currTime or prerace <= currTime):
            print(value["name"].upper())
            printFlairFreq(getRange(prerace, race, flairs))
            print()
        else:
            break
        counter += 1
        prevRace = race


    printFlairFreq(getAll(flairs))

    print("Done!")

main(sys.argv)
