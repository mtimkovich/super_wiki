import os
import webapp2
import jinja2
import logging

import models

from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = False)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class Signup(Handler):
    def get(self):
        self.render('signup.html')

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')

        params = {'username': username}

        if not username:
            params['error_username'] = 'Must have a username'

        if not password or not verify:
            params['error_password'] = 'Must have a password'
        elif password != verify:
            params['error_verify'] = 'The passwords do not match'

        if len(params) > 1:
            self.render('signup.html', **params)
        else:
            u = models.User.by_name(username)

            if u:
                msg = 'That username is taken'
                self.render('signup.html', error_username = msg)
            else:
                u = models.User.register(username, password)
                u.put()

def get_article(path, update = False):
    article = memcache.get(path)

    if article is None or update:
        logging.info('DB QUERY')
        article = models.Article.all().filter('path =', path).get()

        memcache.set(path, article)

    return article

class EditPage(Handler):
    def get(self, path):
        content = get_article(path).content

        self.render('edit.html', path = path, content = content)

    def post(self, path):
        article = get_article(path)

        article.content = self.request.get('content')

        self.write(article.content)

        article.save()

        # Update memcache
        get_article(path, True)

        self.redirect(path)

class WikiPage(Handler):
    def get(self, path):
        a = get_article(path)

        if not a:
            a = models.Article(path = path)

            a.put()

        self.render('wiki.html', path = path, content = a.content)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication(
    [
        ('/signup', Signup),
#         ('/login', Login),
#         ('/logout', Logout),
        ('/_edit' + PAGE_RE, EditPage),
        (PAGE_RE, WikiPage),
    ],
    debug=True)
