import praw
import time
import psycopg2
import sys
import os
import credentials  ## This is a separate file that holds the credentials for accessing the database
			## Rather than build a parser manually, it relys on python functions to
			## retrieve the data

## Globals
WAIT_TIME = 60

## Praw setup
USER_AGENT = ("F1Bot 0.1")
REDDIT = praw.Reddit(USER_AGENT)
SUBREDDIT = REDDIT.get_subreddit("formula1")

## Psycopg2 setup
try:
	DB = psycopg2.connect(database=credentials.database(), host=credentials.hostname(),
			      user=credentials.username(), password=credentials.password())
	CUR = DB.cursor()
except:
	print "Unable to connect to database"
	print sys.exc_info()[1]
	sys.exit()


class Comment:
	""" Simple structure to hold relevant comment data """
	def __init__(self, post_id, author, created_utc, flair_text, body):
		self.id = str(post_id)
		self.author = str(author)
		self.time = int(created_utc)
		self.flair = str(flair_text.encode('ascii','ignore'))
		self.text = str(body.encode('ascii','ignore')).strip('\n').encode('string-escape')

	def getter(self):
		return self.val

	def setter(self, value):
		return self.val

	def deleter(self):
		del self.val

	id = property(getter, setter, deleter, "Post ID of comment")
	author = property(getter, setter, deleter, "Author of comment")
	time = property(getter, setter, deleter, "Time created (UTC) of comment")
	flair = property(getter, setter, deleter, "Flair of author of comment")
	text = property(getter, setter, deleter, "Text of comment")

	def printAll(self):
		print self.id
		print self.author
		print self.time
		print self.flair
		print self.text

class STNode:
        """ Structure to hold the data for each node """
        def __init__(self, key, Value):
                self.key = key
                self.value = value
                self.left = None
		self.right = None

	def getter(self):
                return self.val

        def setter(self, value):
                return self.val

        def deleter(self):
                del self.val

        key = property(getter, setter, deleter, "Key used to categorize the node")
        value = property(getter, setter, deleter, "Value of the node")
        left = property(getter, setter, deleter, "Link to the left child node")
	right = property(getter, setter, deleter, "Link to the right child node")


class ST(STNode):  ## INCOMPLETE -- Relying on slower comparison method for debugging.
	""" Simple search tree to make parsing valid comments easier and faster """
	def __init__(self, comment):
		self.init = STNode(comment.id, comment)

	def _hash(self, value):
		stringList = [str(i) for i in str(value)]
		hash = 0
		for i in stringList:
			hash += int(i) * 101
		return hash

	def findNode(self, comment):
		key = _hash(comment.id)
		node = self.init
		label = node.key
		left = node.left
		right = node.right
	
	## FINISH


def getComments():  ## Gets 25 most recent comments from subreddit
	prawComments =  SUBREDDIT.get_comments()
	comments = []
	for i in prawComments:
		comments.append(i)
	return comments

def trimComments(comments):  ## Returns a list with irrelevant comments removed (No flair)
	trimmed = []
	for i in comments:
		if i.author_flair_text != None:
			trimmed.append(Comment(i.id, i.author, i.created_utc, 
					       i.author_flair_text, i.body))
	return trimmed


def removeDuplicates(comments):  ## Removes comments that have already been archived
	CUR.execute("SELECT post_id FROM f1_bot;")
	for entry in CUR:
		for i in xrange(len(comments)-1,-1,-1):
			if entry[0] == comments[i].id:
				del comments[i]
	return comments


def addComments(comments):  ## Adds comments to the database
	for i in comments:
		i.printAll()
		print

		CUR.execute("INSERT INTO f1_bot (post_id, author, time_created, flair,"
			    " body) VALUES (%s, %s, %s, %s, %s);", (i.id, i.author, 
			    i.time, i.flair, i.text))
	DB.commit()


def main():
	while(True):
		print " > Retrieving comments from the subreddit."
		com = getComments()

		print " > Removing comments that didn't have author flair -",
		trimCom = trimComments(com)
		print 25 - len(trimCom), "comments removed."

		print " > Removing already archived comments -",
		rmCom = removeDuplicates(trimCom)
		print len(trimCom)- len(rmCom), "comments removed." 

		print " > Adding", len(rmCom), "comments to database:", credentials.database()
		print
		addComments(rmCom)

		for i in range(WAIT_TIME):
			sys.stdout.write("\rNext comment retrieval in: %s " %(WAIT_TIME - i))
			sys.stdout.flush()
			time.sleep(1)
		print


main()
