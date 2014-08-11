#!/usr/bin/env python
# -*- coding:utf-8 -*-
import webapp2
import jinja2
import facebook
import os
import logging
from google.appengine.api import lib_config
from google.appengine.ext import db
from webapp2_extras import sessions
from google.appengine.api import users

_config = lib_config.register('main', {'FACEBOOK_ID':None, 'FACEBOOK_SECRECT':None})

class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)

JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions = ['jinja2.ext.autoescape'])

class BaseHandler(webapp2.RequestHandler):
    def require_admin(self):
        user = users.get_current_user()
        logging.info(user)
        if user:
            if users.is_current_user_admin():
                return True
            else:
                self.redirect('/error?id=1')
        else:
            self.redirect(users.create_login_url(self.request.uri))

    def is_admin(self):
        user = users.get_current_user()    
        if user and users.is_current_user_admin():
            return True
        else:
            return False

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    """Provides access to the active Facebook user in self.current_user
    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        if self.session.get("user"):
            # User is logged in
            logging.info("User is logged in. 사용자 로그인 ")
            return self.session.get("user")
        else:
            # Either used just logged in or just saw the first page
            # We'll see here
            logging.info("Check if user is logged in to Facebook.")
            cookie = facebook.get_user_from_cookie(self.request.cookies,
                                                   _config.FACEBOOK_ID,
                                                   _config.FACEBOOK_SECRECT)
            if cookie:
                # Okay so user logged in.
                # Now, check to see if existing user
                user = User.get_by_key_name(cookie["uid"])
                if not user:
                    # Not an existing user so get user info
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = User(
                        key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        access_token=cookie["access_token"]
                    )
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    logging.info('Existing app user with new access token')
                    # get long live token
                    graph = facebook.GraphAPI(cookie["access_token"])
                    token = graph.extend_access_token(app_id=FACEBOOK_APP_ID,app_secret=FACEBOOK_APP_SECRET)['access_token']
                    graph.access_token = token
                    # TODO how to update existing cookie, unless it is okay to keep extending
                    # save user in objectstore
                    user.access_token = token
                    user.put()
                # User is now logged in
                self.session["user"] = dict(
                    name=user.name,
                    profile_url=user.profile_url,
                    id=user.id,
                    access_token=user.access_token
                )
                return self.session.get("user")
        logging.info("No user logged in.")
        return None

    def dispatch(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        """
        This snippet of code is taken from the webapp2 framework documentation.
        See more at
        http://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

        """
        return self.session_store.get_session()

class Home(BaseHandler):
    def get(self):
        super(Home, self).require_admin()
        template = JINJA_ENVIRONMENT.get_template('/view/admin.html')
        self.response.write(template.render({
            'FACEBOOK_ID':_config.FACEBOOK_ID
        }))

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')
app = webapp2.WSGIApplication(
    [('/admin', Home)],
    debug=True,
    config=config
)