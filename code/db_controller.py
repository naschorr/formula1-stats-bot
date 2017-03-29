from __future__ import print_function

from utilities import Utilities
from exception_helper import ExceptionHelper

import json
import sys
import os

if(os.name == "posix"):
    ## https://mail.python.org/pipermail/pypy-dev/2013-May/011398.html
    import psycopg2cffi as psycopg2
elif(os.name == "nt"):
    import psycopg2
else:
    ## No idea what os it is, just try psycopg2
    import psycopg2


class DB_Controller:
    ## Globals
    DB_CFG_NAME = "db.json"
    REMOTE_DB_CFG_NAME = "remote_db.json"
    DB_CFG_PATH = Utilities.build_path_from_config(DB_CFG_NAME)

    def __init__(self, **kwargs):
        static = DB_Controller

        ## Handle the args
        self.remote = kwargs.get("remote", False)

        ## Init the exception helper
        self.exception_helper = ExceptionHelper(log_time=True, std_stream=sys.stderr)

        ## Get config data for the database
        if(self.remote):
            static.DB_CFG_PATH = Utilities.build_path_from_config(static.REMOTE_DB_CFG_NAME)
        self.db_cfg = Utilities.load_json(static.DB_CFG_PATH)

        ## Open a connection to the database
        try:
            self.db = psycopg2.connect(database=self.db_cfg["database"],
                                       host=self.db_cfg["hostname"],
                                       user=self.db_cfg["username"],
                                       password=self.db_cfg["password"])
        except psycopg2.OperationalError as e:
            self.exception_helper.print(e, "Unable to connect to the database.\n", exit=True)
        except Exception as e:
            self.exception_helper.print(e, "Unexpected error when trying to connect to the database.\n", exit=True)

        ## Get the table that'll be worked with
        self.table = self.db_cfg["table"]

        ## Display row count on startup (if not disabled)
        if(not kwargs.get("suppress_greeting", False)):
            print("Currently {0} rows in table {1}.".format(self.count_rows(), self.table))


    def count_rows(self, table=None):
        if(not table):
            table = self.table

        with self.db.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM {0};".format(table))
            return cursor.fetchone()[0]


    def store_comment(self, comment_obj, table=None):
        if(not table):
            table = self.table

        ## Stage changes to the db
        with self.db.cursor() as cursor:
            raw =  """INSERT INTO {0} (post_id, author, time_created, flair,
                      body) VALUES (%s, %s, %s, %s, %s);"""
            try:
                cursor.execute(raw.format(table), (comment_obj.id.id,
                                                   comment_obj.author,
                                                   comment_obj.time,
                                                   comment_obj.flair,
                                                   comment_obj.text))
            except psycopg2.IntegrityError as e:
                self.exception_helper.print(e, "Primary key integrity error.\n")
                self.db.rollback()
            except Exception as e:
                self.exception_helper.print(e, "Unexpected error when storing comment into the database.\n", exit=True)
            else:

                ## Commit changes to the db
                try:
                    self.db.commit()
                except Exception as e:
                    self.exception_helper.print(e, "Unexpected error when committing changes to the database.\n", exit=True)
                else:

                    ## Output the successfully added comment
                    comment_obj.dump()


    def delete_row(self, post_id, table=None):
        if(not table):
            table = self.table

        ## Stage changes to the db
        with self.db.cursor() as cursor:
            raw = "DELETE FROM {0} WHERE post_id = %s;"
            try:
                cursor.execute(raw.format(table), (post_id,))
            except Exception as e:
                self.exception_helper.print(e, "Unexpected error when removing row with post_id: {0} from the database.\n".format(post_id), exit=True)
            else:

                ## Commit changes to the db
                try:
                    self.db.commit()
                except Exception as e:
                    self.exception_helper.print(e, "Unexpected error when committing changes to the database.\n", exit=True)