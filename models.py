from google.appengine.ext import db

class Article(db.Model):
    path = db.StringProperty(required = True)
    content = db.TextProperty(default = '')
    created = db.DateTimeProperty(auto_now_add = True)
