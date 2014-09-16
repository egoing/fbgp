import cgi

from google.appengine.api import users

import webapp2

MAIN_PAGE_HMTL = """\
<html>
<body>
	<form action="/sign" method="post">
		<div><textarea name="content" rows="8" cols="60"></textarea></div>
		<div><input type="submit" value="Sign Guestbook"></div>
	</form>
</body>
</html>
"""

class MainPage(webapp2.RequestHandler):

    def get(self):
        self.response.write(MAIN_PAGE_HMTL)

class Guestbook(webapp2.RequestHandler):

	def post(self):
		self.response.write('<html><body>You write:<pre>')
		self.response.write(cgi.escape(self.request.get('content')))
		self.response.write('</pre></body></html>')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', Guestbook),
], debug=True)