from google.appengine.ext import db

class Article(db.Model):
    page = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
