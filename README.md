# /r/formula1 stats bot
Analyzes trends in driver and team popularity by analyzing subreddit user flair.

Start by renaming example_credentials.py to credentials.py, and fill in the relevant database and user information. Next, assuming everything is set up properly, it'll start pulling data from reddit.

Using praw (2.1.19), a postgres (9.1.14) database, and psycopg2 (2.5.1) to interface with the database.

To do:

- Build simple statistics suite to analyze collected data.
  
- Implement some sort of search algorithm to ensure no duplicate comments are added.
  
- Give functionality to parse through older comments.
  
- Fix output. ("Removing already archived comments" gives an incorrect value)
  
    - Possibly simplify output and add a verbose option?

- Handle connection error with an immediate re-request? Need to confirm that praw doesn't already do this.

- Dynamically change the wait time between requests based on frequency of new comments.
