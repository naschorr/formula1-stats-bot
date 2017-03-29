from __future__ import print_function

import sys


class CommentId:
    def __init__(self, comment_id):
        self.id = comment_id

    def __repr__(self):
        return self.base10()

    ## Properties

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        ## TODO: better sanitization
        self._id = str(value)

    ## Methods

    def base10(self):
        return int(self.id, 36)


class Comment:
    ## TODO: Better input sanitization
    def __init__(self, post_id, author, created_utc, flair_text, body):
        self.id = CommentId(post_id)
        self.author = str(author)
        self.time = int(created_utc)
        self.flair = str(flair_text).strip()
        self.text = str(body).strip()

    def __repr__(self):
        raw = "{}: id={}, author={}, time={}, flair={}, body_len={}"
        return raw.format(self.__class__.__name__, self.id.id, self.author,
                          self.time, self.flair, len(self.text))

    ## Properties

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

    @property
    def author(self):
        return self._author

    @author.setter
    def author(self, value):
        self._author = value

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = value

    @property
    def flair(self):
        return self._flair

    @flair.setter
    def flair(self, value):
        self._flair = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    ## Methods

    def strip(self, string):
        return string.lstrip().rstrip()

    def dump(self):
        try:
            print("-------------")
            print(self.id.id, self.id.base10())
            print(self.author)
            print(self.time)
            print(self.flair)
            print(self.text)
            sys.stdout.flush()
        except UnicodeEncodeError as e:
            print(e, "Error rendering this comment's unicode. Skipping...\n")