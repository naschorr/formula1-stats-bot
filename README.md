# /r/formula1 stats bot

Analyzes trends in driver and team popularity by analyzing subreddit user flair.

------
####To use:

Start by removing "example_" from example_credentials.py, and fill in the relevant database and user information. Do the same for the example_remote_credentials.py. Next, assuming everything is set up properly (see table information below), it'll start pulling data from reddit. Use "-v" after the filename to use verbose output. Using remote_bot.py isn't necessary, but it makes pulling data off of a Raspberry Pi (or whatever you might be running it on) and storing it more permanantly much easier. I'd recommend setting up a cron job to run the remote_bot.py at some reasonable interval, but it's up to you.

  ex: python bot.py -v
  
  ex: python remote_bot.py

This project uses praw (2.1.20), a postgres (9.1.14) database, and psycopg2 (2.5.1) to interface with the database.

------

####To do:

- Build simple statistics suite to analyze collected data.
  
- Implement some sort of search algorithm to ensure no duplicate comments are added. (Possibly not necessary with base-36 converter and new sorting system.)
  
- Give functionality to parse through older comments.

- Improve function for the wait timer (currently linear, maybe something closer to x^-2?)

- Add in wait timer override when pulling in a certain amount of comments?

- Add table information to credentials.py.

- Output table to a .csv file.

------

createtable f1_bot (
  post_id varchar(15) PRIMARY KEY,
  author varchar(20) NOT NULL,
  time_created integer NOT NULL,
  flair varchar(25) NOT NULL,
  body text
  );
