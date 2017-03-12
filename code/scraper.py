from __future__ import print_function

import json
import sys
import os
import click
import praw
import requests

from time import sleep

if(os.name == "posix"):
    ## https://mail.python.org/pipermail/pypy-dev/2013-May/011398.html
    import psycopg2cffi as psycopg2
elif(os.name == "nt"):
    import psycopg2
else:
    ## No idea what os it is, just try psycopg2
    import psycopg2

from comment import Comment

## Globals
CONFIG_FOLDER_NAME = "config"
DB_CONFIG_NAME = "db.json"
REMOTE_DB_CONFIG_NAME = "remote_db.json"
REDDIT_CONFIG_NAME = "reddit.json"
ATTEMPT_LIMIT = 10
SLEEP_TIME = 10

DB_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, DB_CONFIG_NAME])
REDDIT_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, REDDIT_CONFIG_NAME])

class DB_Controller:
    def __init__(self, db_cfg_path):
        with open(db_cfg_path) as db_json:
            self.db_cfg = json.load(db_json)

        try:
            self.db = psycopg2.connect(database=self.db_cfg["database"],
                                       host=self.db_cfg["hostname"],
                                       user=self.db_cfg["username"],
                                       password=self.db_cfg["password"])
        except psycopg2.OperationalError as poe:
            print("Unable to connect to database:", poe, file=sys.stderr)
            sys.exit()
        except:
            print("Unhandled error when connecting to database", sys.exc_info()[1], file=sys.stderr)
            sys.exit()

        self.table = self.db_cfg["table"]

        print("Currently {0} rows in table {1}.".format(self.count_rows(), self.table))


    def count_rows(self):
        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM {0};".format(self.table))
            return cursor.fetchone()[0]


    def store_comment(self, comment_obj):
        ## Stage changes to the db
        with self.db.cursor() as cursor:
            raw =  """INSERT INTO {0} (post_id, author, time_created, flair, 
                      body) VALUES (%s, %s, %s, %s, %s);"""
            try:
                cursor.execute(raw.format(self.table), (comment_obj.id.id,
                                                        comment_obj.author,
                                                        comment_obj.time,
                                                        comment_obj.flair,
                                                        comment_obj.text))
            except psycopg2.IntegrityError as pie:
                print("Primary Key integrity violation. Ignoring this comment.", pie, file=sys.stderr)
                self.db.rollback()
            except:
                print("Unhandled error when inserting into db", sys.exc_info(), file=sys.stderr)
                sys.exit()
            else:

                ## Commit changes to the db
                try:
                    self.db.commit()
                except:
                    print("Unhandled error when commiting changes to db", sys.exc_info(), file=sys.stderr)
                    sys.exit()
                else:

                    ## Output the successfully added comment
                    self.dump_comment(comment_obj)


    def dump_comment(self, comment_obj):
        try:
            comment_obj.print_all()
            sys.stdout.flush()
        except UnicodeEncodeError as uee:
            print("Error encoding a character", uee, "\nSkipping...")


class Scraper:
    def __init__(self, db_controller, reddit_cfg_path):
        ## Hard limit to attempt to stream comments (so the script doesn't
        ##  just endlessly accomplish nothing)
        self._attempts = 0

        ## Get the config data for the reddit instance
        with open(reddit_cfg_path) as reddit_json:
            self.reddit_cfg = json.load(reddit_json)

        ## Get Reddit instance
        try:
            self.reddit = praw.Reddit(client_id=self.reddit_cfg["id"],
                                      client_secret=self.reddit_cfg["secret"],
                                      user_agent=self.reddit_cfg["useragent"],
                                      username=self.reddit_cfg["username"],
                                      password=self.reddit_cfg["password"])
        except:
            print("Unhandled error when getting Reddit instance", sys.exc_info()[1], file=sys.stderr)
            sys.exit()

        ## Get Subreddit instance
        try:
            self.subreddit = self.reddit.subreddit(self.reddit_cfg["subreddit"])
        except:
            print("Unhandled error when getting subreddit instance", sys.exc_info()[1], file=sys.stderr)
            sys.exit()

        ## Save the db_controller
        self.db = db_controller

        ## Start parsing the new comment stream
        self.stream_comments()


    ## TODO: Make this less ugly
    def stream_comments(self):
        try:
            for comment in self.subreddit.stream.comments():
                self.parse_comment(comment, self.db.store_comment)
                if(self._attempts > 0):
                    self._attempts -= 1
        except (requests.RequestException, Exception) as e:
            print("Praw Request exception", e, file=sys.stderr)
            if(self._attempts < ATTEMPT_LIMIT):
                self._attempts += 1
                sleep(SLEEP_TIME)
                self.stream_comments()
            else:
                print("Too many errors, quitting", e, file=sys.stderr)
                sys.exit()


    def parse_comment(self, praw_comment, callback):
        if(praw_comment.author_flair_text != None):
            comment_obj = Comment(praw_comment.id,
                                  praw_comment.author,
                                  praw_comment.created_utc,
                                  praw_comment.author_flair_text,
                                  praw_comment.body)
            if(callback):
                callback(comment_obj)


@click.command()
@click.option("--remote", "-r", is_flag=True, help="Denotes whether or not the scraper is accessing the database remotely (using {0} instead of {1})".format(REMOTE_DB_CONFIG_NAME, DB_CONFIG_NAME))
def main(remote):
    ## Handle args
    if(remote):
        global DB_PATH
        DB_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, REMOTE_DB_CONFIG_NAME])

    ## Init DB_Controller
    db_controller = DB_Controller(DB_PATH)

    ## Init Scraper
    scraper = Scraper(db_controller, REDDIT_PATH)


if __name__ == '__main__':
    main()
