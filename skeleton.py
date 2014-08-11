import webapp2
import jinja2
import os

class HelloWebapp2(webapp2.RequestHandler):
    def get(self):
        self.response.write('Hello, webapp2!')


jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')
app = webapp2.WSGIApplication(
    [('/admin', HelloWebapp2), ('/', HelloWebapp2)],
    debug=True,
    config=config
)