import hashlib

from google.appengine.ext import db

class Article(db.Model):
    path = db.StringProperty(required = True)
    content = db.TextProperty(default = '')
    created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    username = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    @classmethod
    def by_name(cls, username):
        return User.all().filter('username =', username).get()

    @classmethod
    def register(cls, username, password):
        pw_hash = hashlib.sha256(password).hexdigest()

        return User(username = username,
                    pw_hash = pw_hash)
