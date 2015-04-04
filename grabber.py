import praw
import time
import psycopg2
import sys
import operator
import comment
import credentials as c  ## This is a separate file that holds the credentials for accessing the database
            ## Rather than build a parser manually, it relys on python functions to
            ## retrieve the data. Look at "example_credentials.py" to get it set up.

## Globals
WAIT_INTERVAL = 1
MAX_WAIT_TIME = 60
WAIT_TIME = 30
MIN_WAIT_TIME = 2  ## Minimum time between requests (according to reddit API)
ROWS = 0

## Praw setup
USER_AGENT = ("F1Bot 0.1")
REDDIT = praw.Reddit(USER_AGENT)
SUBREDDIT = REDDIT.get_subreddit("formula1")

## Psycopg2 setup
try:
    DB = psycopg2.connect(database=c.database(), host=c.hostname(),
                  user=c.username(), password=c.password())
    CUR = DB.cursor()
except:
    print "Unable to connect to database"
    print sys.exc_info()[1]
    sys.exit()


## Desc - Counts the number of rows in the database
## In   - Nothing (cursor defined globally)
## Out  - long int rows
## Mod  - Nothing
## ToDo - Nothing
def countRows():
    CUR.execute("SELECT COUNT(*) FROM f1_bot;")
    return CUR.fetchone()[0]


## Desc - Gets 25 most recent comments from subreddit
## In   - Nothing (subreddit defined globally)
## Out  - (praw comment) list comments
## Mod  - Nothing
## ToDo - Return status code?
##      - Build comment objects here
def getComments():
    prawComments =  SUBREDDIT.get_comments()
    comments = []
    try:
        for i in prawComments:
            comments.append(i)
    except ValueError as ve:
        print "ValueError occurred - ", ve
    except:
        print "Generic Exception in getComments() - This shouldn't ever trigger. Ignoring current comments."
    return comments


## Desc - Removes comments without user flair
## In   - (comment) list comments
## Out  - (comment) list trimmed
## Mod  - Nothing
## ToDo - Return status code?
##      - Refactor to return (comment) list comments?
##      - Remove comment object generation, and let getComments() handle it?
def trimComments(comments):
    trimmed = []
    for i in comments:
        if i.author_flair_text != None:
            trimmed.append(comment.Comment(i.id, i.author, i.created_utc, 
                           i.author_flair_text, i.body))
    return trimmed


## Desc - Removes comments that have already been archived inside the database
## In   - (comment) list comments
## Out  - (comment) list comments with duplicates removed
## Mod  - Nothing
## ToDo - Return status code?
##      - Use variable to select columns and table?
##      - Fix code that pulls rows from database - (startRow >= ROWS -25) is baaaad.
def removeDuplicates(comments):
    CUR.execute("SELECT post_id from f1_bot ORDER BY post_id DESC LIMIT 1;")
    lastValue = int(CUR.fetchone()[0], 36)
    length = len(comments)-1
    while(length >= 0 and comments[length].decodeId() <= lastValue):
        del comments[length]
        length -= 1

    return comments



## Desc - Sorts comments by their post_id (converted to base-10) values
## In   - (comments) list of comment objects
## Out  - (comments) list of sorted comment objects
## Mod  - Nothing
## ToDo - Return staus code?
def sortComments(comments):
    return sorted(comments, key=operator.methodcaller('decodeId'))


## Desc - Adds comments to the databse
## In   - (comment) list comments
## Out  - Prints "valid" comments
## Mod  - Inserts comment data into database's table
## ToDo - Return a status code?
##      - Use variable to select columns and table?
def addComments(comments):
    for i in comments:
        try:
            CUR.execute("INSERT INTO f1_bot (post_id, author, time_created, flair,"
                    " body) VALUES (%s, %s, %s, %s, %s);", (i.id, i.author, 
                    i.time, i.flair, i.text))
        except Exception, e:
            print "Exception in addComments() - Likely an IntegrityError. Ignoring comments."
            print e.pgerror
            continue
        except:
            print "Generic exception in addComments() - This shouldn't ever trigger. Ignoring current comment."
            continue

    DB.commit()


## Desc - Adjusts wait time between comment retrievals based on comment frequency
## In   - (int) list times
## Out  - Nothing
## Mod  - global WAIT_TIME, with newly calculated wait time (int)
## ToDo - Alter to get rid of globals, and simply return the wait time.
##      - Improve wait time calculation (currently linear)
##      - Return a status code?
def adjustWaitTime(times):
    global WAIT_TIME

    avg = 0.0
    for i in times:
        avg += i
    avg = avg/len(times)
    wait = int(((MAX_WAIT_TIME) / -25) * avg + (MAX_WAIT_TIME))
    if MAX_WAIT_TIME >= wait >= MIN_WAIT_TIME:
        WAIT_TIME = wait
    elif wait < MIN_WAIT_TIME:
        WAIT_TIME = MIN_WAIT_TIME
    else:
        WAIT_TIME = MAX_WAIT_TIME


## Desc - Outputs status of comment retrieval, as well as accepted comments. 
##          Responsible for calling comments for retrival.
## In   - Nothing
## Out  - Printed status of comment retrival, and accepted comments
## Mod  - Nothing
## ToDo - Nothing
def verboseMode():
    global ROWS

    print " > Retrieving comments from the subreddit."
    com = getComments()

    print " > Removing comments that didn't have author flair -",
    trimCom = trimComments(com)
    lenTrimCom = len(trimCom)
    print 25 - lenTrimCom, "comments removed."

    print " > Removing already archived comments -",
    rmCom = removeDuplicates(trimCom)
    lenRmCom = len(rmCom)
    print lenTrimCom - lenRmCom, "comments removed."
    ROWS += lenRmCom

    print " > Sorting comments by their post id -",
    sortCom = sortComments(rmCom)
    lenSortCom = len(sortCom)
    print lenSortCom, "comments sorted."

    print " > Adding", lenSortCom, "comments to database:", c.database()
    addComments(sortCom)
    print " > There are", ROWS, "comments in database:", c.database()

    print " > Printing", lenSortCom, "comments to terminal."
    if lenSortCom > 0:
        for i in sortCom:
            i.printAll()
            print

    return sortCom

## Desc - Stealthily calls comment retrieval functions, and only displays the number 
##          of accepted comments.
## In   - Nothing
## Out  - Print number accepted comments
## Mod  - Nothing
## ToDo - Nothing
def quietMode():
    global ROWS

    com = sortComments(removeDuplicates(trimComments(getComments())))
    lenCom = len(com)
    ROWS += lenCom
    print " > Adding", lenCom, "comments to:", c.database()
    addComments(com)

    return com


## Desc - Timer to handle the wait between comment requests from reddit
## In   - int sleepInterval
## Out  - printed line giving the time left until next retrieval
## Mod  - Nothing
## ToDo - Nothing
def waitFor(sleepInterval):
    try:
        for i in range(WAIT_TIME):
            sys.stdout.write("\rNext comment retrieval in: %s " %(WAIT_TIME - i))
            sys.stdout.flush()
            time.sleep(sleepInterval)
        sys.stdout.write("\r")
        sys.stdout.flush()

    except KeyboardInterrupt:
        print "\nHalted by user."
        sys.exit()

    except:
        print "\nUnhandled exception."
        sys.exit()


def main(args):
    global ROWS
    
    ROWS = countRows()
    recentComments = []
    while(True):
        if "-v" in args:
            comments = verboseMode()
        else:
            comments = quietMode()

        if len(recentComments) < 3:
            recentComments.append(len(comments))
        else:
            del recentComments[0]
            recentComments.append(len(comments))

        adjustWaitTime(recentComments)
        
        waitFor(WAIT_INTERVAL)
        
main(sys.argv)
