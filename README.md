# /r/formula1 stats bot

Analyzes trends in driver and team popularity by analyzing subreddit user flair.

------
####To use:

Start by renaming example_credentials.py to credentials.py, and fill in the relevant database and user information. Next, assuming everything is set up properly (see table information below), it'll start pulling data from reddit. Use "-v" after the filename to use verbose output.

  ex: python bot.py -v

This project uses praw (2.1.20), a postgres (9.1.14) database, and psycopg2 (2.5.1) to interface with the database.

------

####To do:

- Build simple statistics suite to analyze collected data.
  
- Implement some sort of search algorithm to ensure no duplicate comments are added.
  
- Give functionality to parse through older comments.

- Improve function for the wait timer (currently linear, maybe something closer to x^-2?)

- Add table information to credentials.py.

------

createtable f1_bot (
  post_id varchar(15) PRIMARY KEY,
  author varchar(20) NOT NULL,
  time_created integer NOT NULL,
  flair varchar(25) NOT NULL,
  body text
  );
