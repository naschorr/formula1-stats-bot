import praw

user_agent = ("PyBot 0.1")

r = praw.Reddit(user_agent=user_agent)

subreddit = r.get_subreddit("formula1")

comments = subreddit.get_comments()

for com in comments:
	if com.author_flair_text != None:
		print "---"
		print com.author_flair_text
		print "---"
		print com.author,
		print " - " + str(com.created)
		print com.body
		print '\n'
