# /r/formula1 stats bot
Analyzes trends in driver and team popularity by analyzing subreddit user flair.

Start by renaming example_credentials.py to credentials.py, and fill in the relevant database and user information. Next, assuming everything is set up properly, it'll start pulling data from reddit.

Requires praw, a postgres database, and psycopg2 to interface with the databse.

To do:

- Build simple statistics suite to analyze collected data.
  
- Implement some sort of search algorithm to ensure no duplicate comments are added.
  
- Give functionality to parse through older comments.
  
- Fix output. ("Removing already archived comments" gives an incorrect value)
  
    - Possibly simplify output and add a verbose option?

- Handle connection error with an immediate re-request? Need to confirm that praw doesn't already do this.
