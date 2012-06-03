from google.appengine.ext import db

class Article(db.Model):
    path = db.StringProperty(required = True)
    content = db.TextProperty(default = '')
    created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    name = db.StringProperty(required = True)
    pass_hash = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
