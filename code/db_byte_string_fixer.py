from __future__ import print_function

import sys
import click

from db_controller import DB_Controller
from exception_helper import ExceptionHelper
from comment import Comment


class DB_Byte_String_Fixer:
    MAIN_DB_TABLE = "comments"
    ALT_DB_TABLE = "invalid_comments"

    COMMENTS_ID = "post_id"

    ## Windows versions of scraper.py stored some improperly formatted strings
    ## (Python byte strings) in the 'comments' table. I moved the byte strings
    ## into a table with an idential schema to 'comments' called 
    ## 'invalid_comments' with the following SQL query:

    """
    INSERT INTO invalid_comments (post_id, author, time_created, flair, body)
    SELECT post_id, author, time_created, flair, body FROM (
        SELECT post_id, author, time_created, flair, body, 
        substring(flair FROM '^b''.*?''$') as flair_sub,
        substring(body FROM '^b''.*?''$') as body_sub
        FROM comments
    ) ss
    WHERE LENGTH(flair_sub) > 0 OR LENGTH(body_sub) > 0;
    """

    ## Then deleted them from the original 'comments' table using:

    """
    DELETE FROM comments
    USING invalid_comments
    WHERE comments.post_id = invalid_comments.post_id;
    """

    def __init__(self, **kwargs):
        self.static = DB_Byte_String_Fixer

        self.exception_helper = ExceptionHelper(log_time=True, std_stream=sys.stderr)

        self.db_controller = DB_Controller(**kwargs)
        self.db = self.db_controller.db

        self.get_byte_strings(self.repair_record_byte_strings, self.static.ALT_DB_TABLE)


    def get_byte_strings(self, callback, table):
        with self.db.cursor() as cursor:
            raw = """SELECT * FROM (
                        SELECT post_id, author, time_created, flair, body, 
                        substring(flair FROM '^b''.*?''$') as flair_sub, 
                        substring(body FROM '^b''.*?''$') as body_sub FROM 
                        {0}) ss 
                     WHERE LENGTH(flair_sub) > 0 OR LENGTH(body_sub) > 0;"""
            try:
                cursor.execute(raw.format(table))
            except Exception as e:
                self.exception_helper.print(e, "Unexpected error when retrieving byte strings from the database.\n", exit=True)
            else:

                for row in cursor:
                    callback(row)


    def repair_record_byte_strings(self, record):
        def repair_byte_string(byte_string):
            try:
                return eval(byte_string).decode("utf-8", "ignore")
            except (NameError, SyntaxError) as e:
                return byte_string
            except Exception as e:
                self.exception_helper.print(e, "Unexpected error when converting a byte string:".format(byte_string))
                return None

        flair = repair_byte_string(record[3])
        body = repair_byte_string(record[4])

        if(flair == None or body == None):
            return

        comment_obj = Comment(record[0], record[1], record[2], flair, body)

        try:
            self.db_controller.delete_row(self.static.COMMENTS_ID, comment_obj.id.id, self.static.ALT_DB_TABLE)
            self.db_controller.store_comment(comment_obj)
        except Exception as e:
            self.exception_helper.print(e, "Unexpected error when moving comments between tables.\n", exit=True)


@click.command()
@click.option("--remote", "-r", is_flag=True,
              help="Denotes whether or not the scraper is accessing the database remotely (using {0} instead of {1})".format(DB_Controller.REMOTE_DB_CFG_NAME, DB_Controller.DB_CFG_NAME))
def main(remote):
    kwargs = {"remote": remote}

    DB_Byte_String_Fixer(**kwargs)


if __name__ == "__main__":
    main()