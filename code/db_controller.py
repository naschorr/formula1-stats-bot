from __future__ import print_function

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