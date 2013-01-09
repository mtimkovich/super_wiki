import os
import webapp2
import jinja2
import logging
import hashlib
import hmac
import urllib

import models

from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = False)

secret = 'supersecret'

def remove_slash(path):
    return path[1:]

def make_secure_val(val):
    return "{}|{}".format(val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        kw['user'] = self.user
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            "{0}={1}; Path=/".format(name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and models.User.by_id(int(uid))

class Signup(Handler):
    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')

        errors = {'username': username}

        if not username:
            errors['error_username'] = 'Must have a username'

        if not password or not verify:
            errors['error_password'] = 'Must have a password'
        elif password != verify:
            errors['error_verify'] = 'The passwords do not match'

        if len(errors) > 1:
            self.render('signup.html', **errors)
        else:
            u = models.User.by_name(username)

            if u:
                msg = 'That username is taken'
                self.render('signup.html', error_username = msg)
            else:
                u = models.User.register(username, password)
                u.put()

                self.login(u)
                self.redirect('/')

class Login(Handler):
    def get(self):
        self.render('login.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        returnurl = self.request.get('returnurl')

        u = models.User.login(username, password)
        if u:
            self.login(u)
            self.redirect('_edit/' + str(returnurl))
        else:
            msg = 'Invalid login'
            self.render('login.html', username = username, error = msg)

class Logout(Handler):
    def get(self):
        self.logout()
        self.redirect('/')

def get_article(path, update = False):
    article = memcache.get(path)

    if article is None or update:
        logging.info('DB QUERY')
        article = models.Article.all().filter('path =', path).get()

        memcache.set(path, article)

    return article

class EditPage(Handler):
    def get(self, path):
        if not self.user:
            self.redirect('/login?returnurl=' + urllib.quote(remove_slash(path), ''))

        article = get_article(path)

        if article:
            content = article.content
        else:
            content = ''

        self.render('edit.html', path = path, content = content)

    def post(self, path):
        article = get_article(path)
        
        if article:
            content = article.content
        else:
            article = models.Article(path = path)
            article.put()

        article.content = self.request.get('content')

        self.write(article.content)

        article.save()

        # Update memcache
        get_article(path, True)

        self.redirect(path)

class WikiPage(Handler):
    def get(self, path):
        a = get_article(path)

        if a:
            self.render('wiki.html', path = path, content = a.content)
        else:
            self.redirect('/_edit' + path)


PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication(
    [
        ('/signup', Signup),
        ('/login', Login),
        ('/logout', Logout),
        ('/_edit' + PAGE_RE, EditPage),
        (PAGE_RE, WikiPage),
    ],
    debug=True)
