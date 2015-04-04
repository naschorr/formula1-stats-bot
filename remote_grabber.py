import psycopg2
import remote_credentials as rc
import credentials as c
import sys
import operator
import comment

## Psycopg2 remote setup
try:
    remoteDB = psycopg2.connect(database=rc.database(), host=rc.hostname(), port=rc.port(),
                  user=rc.username(), password=rc.password())
    remoteCUR = remoteDB.cursor()
except:
    print "Unable to connect to remote database"
    print sys.exc_info()[1]
    sys.exit()


## Psycopg2 local setup
try:
    DB = psycopg2.connect(database=c.database(), host=c.hostname(), user=c.username(), 
            password=c.password())
    CUR = DB.cursor()
except:
    print "Unable to connect to local database"
    print sys.exc_info()[1]
    sys.exit()


## Desc - Gets the remote comments such that start <= x < end, where x is the comments.
## In   - (chunkSize) integer of the number of comments to pull from remote database
## Out  - list of comment objects
## Mod  - Nothing
## ToDo - Return status code?
##      - Add try except block for connection issues?
def getRemoteComments(chunkSize=25):
    comments = []
    remoteCUR.execute("SELECT * FROM f1_bot ORDER BY post_id LIMIT %s OFFSET %s;", (chunkSize, 0))
    for i in remoteCUR:
        comments.append(comment.Comment(i[0], i[1], i[2], i[3], i[4]))
    return comments


## Desc - Sorts comments by their post_id (converted to base-10) values
## In   - (comments) list of comment objects
## Out  - (comments) list of sorted comment objects
## Mod  - Nothing
## ToDo - Return staus code?
def sortComments(comments):
    return sorted(comments, key=operator.methodcaller('decodeId'))

## Desc - Adds in the supplied comments to the local database.
## In   - (comments) list of comment objects
## Out  - Nothing
## Mod  - Local database
## ToDo - Return status code?
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
    DB.commit()

## Desc - Deletes already parsed comments from remote databse (freeing up space)
## In   - (chunkSize) integer of the number of comments to delete from remote database
## Out  - Nothing
## Mod  - Remote database
## ToDo - Use string formatting so that the chunkSize arg is actually used (%s, %(chunkSize))
##      - Return status code?
def deleteRemoteComments(chunkSize=25):
    remoteCUR.execute("DELETE FROM f1_bot WHERE ctid IN (SELECT ctid FROM f1_bot ORDER BY post_id "
                      "LIMIT %s);", (chunkSize,))
    remoteDB.commit()


def main():
    remoteCUR.execute("SELECT COUNT(*) FROM f1_bot;")
    remoteRows = remoteCUR.fetchone()[0]

    chunkSize = 25
    ctr = 0
    while(ctr < remoteRows - chunkSize):
        comments = []
        print " > Getting and sorting comments %s to %s from remote database:" %(ctr, ctr + chunkSize), rc.database()
        comments = sortComments(getRemoteComments(chunkSize))
        print " > Adding comments to local database:", c.database()
        addComments(comments)
        print " > Removing comments from remote database:", rc.database()
        deleteRemoteComments(len(comments))
        ctr += chunkSize
    print " >", ctr, "comments successfully migrated."
    CUR.execute("SELECT COUNT(*) FROM f1_bot;")
    print " > There are now", ctr + CUR.fetchone()[0], "comments in local database:", c.database()


main()
