from __future__ import print_function

import json
import sys
import os
import click
import praw
import requests

from time import sleep

from exception_helper import Exception_Helper
from comment import Comment
from db_controller import DB_Controller

## Globals
CONFIG_FOLDER_NAME = "config"
DB_CONFIG_NAME = "db.json"
REMOTE_DB_CONFIG_NAME = "remote_db.json"
REDDIT_CONFIG_NAME = "reddit.json"

DB_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, DB_CONFIG_NAME])
REDDIT_PATH = os.path.sep.join(os.path.realpath(__file__).split(os.path.sep)[:-2] + [CONFIG_FOLDER_NAME, REDDIT_CONFIG_NAME])


class Scraper:
    def __init__(self, db_controller, reddit_cfg_path):
        ## Init the exception helper
        self.exception_helper = Exception_Helper(log_time=True, std_stream=sys.stderr)

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
        except Exception as e:
            self.exception_helper.print(e, "Unexpected error when getting Reddit instance.\n", exit=True)

        ## Get Subreddit instance
        try:
            self.subreddit = self.reddit.subreddit(self.reddit_cfg["subreddit"])
        except Exception as e:
            self.exception_helper.print(e, "Unexpected error when getting subreddit instance.\n", exit=True)

        ## Save the db_controller
        self.db = db_controller

        ## Start parsing the new comment stream
        self.exception_helper.make_robust(self.stream_comments, [requests.RequestException, Exception], self.exception_helper.print_stdout, self.exception_helper.print_stderr)


    def stream_comments(self):
        for comment in self.subreddit.stream.comments():
            self.parse_comment(comment, self.db.store_comment)


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
