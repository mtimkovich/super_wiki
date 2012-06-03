import os
import webapp2
import jinja2
import logging

import models

from google.appengine.api import memcache

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

def get_articles(update = False):
    key = "all"

    articles = memcache.get(key)

    if articles is None or update:
        logging.info('DB QUERY')
        articles = models.Article.all()

        memcache.set(key, articles)

    return articles

class EditPage(Handler):
    def get(self, path):
        pass

class WikiPage(Handler):
    def get(self, path):
        a = get_articles().filter('path =', path).get()

        if not a:
            a = models.Article(path = path, content = path)

            a.put()

        self.render("wiki.html", path = path, content = a.content)

PAGE_RE = r'(/(?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication(
    [
#         ('/signup', Signup),
#         ('/login', Login),
#         ('/logout', Logout),
        ('/_edit' + PAGE_RE, EditPage),
        (PAGE_RE, WikiPage),
    ],
    debug=True)
