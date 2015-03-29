## Desc - Structure to hold relevant data from reddit comments
## In   - str post_id, str author, str created_utc, str flair_text, str body
## Out  - Nothing
## Mod  - Nothing
## ToDo - Return status code on successful creation?
class Comment:
    """ Simple structure to hold relevant comment data """
    def __init__(self, post_id, author, created_utc, flair_text, body):
        self.id = str(post_id)
        self.author = str(author)
        self.time = int(created_utc)
        self.flair = str(flair_text.encode('ascii','ignore'))
        self.text = str(body.encode('ascii','ignore')).strip('\n').encode('string-escape')

    def __repr__(self):
        raw = "{}: Id={}, Author={}, Time={}, Flair={}, BodyLen={}"
        return raw.format(self.__class__.__name__, self.id, self.author, self.time, self.flair,
                          len(self.text))

    def __cmp__(self, other):
        if hasattr(other, 'id'):
            return self.id.__cmp__(other.id)


    def getter(self):
        return self.val

    def setter(self, value):
        return self.val

    def deleter(self):
        del self.val

    id = property(getter, setter, deleter, "Post ID of comment")
    author = property(getter, setter, deleter, "Author of comment")
    time = property(getter, setter, deleter, "Time created (UTC) of comment")
    flair = property(getter, setter, deleter, "Flair of author of comment")
    text = property(getter, setter, deleter, "Text of comment")

    def printAll(self):
        print "-------------"
        print self.id
        print self.author
        print self.time
        print self.flair
        print self.text

    def decodeId(self):
        return int(self.id, 36)