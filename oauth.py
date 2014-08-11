#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Copyright 2010 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
A barebones AppEngine application that uses Facebook for login.

1.  Make sure you add a copy of facebook.py (from python-sdk/src/)
    into this directory so it can be imported.
2.  Don't forget to tick Login With Facebook on your facebook app's
    dashboard and place the app's url wherever it is hosted
3.  Place a random, unguessable string as a session secret below in
    config dict.
4.  Fill app id and app secret.
5.  Change the application name in app.yaml.

"""

import facebook
import webapp2
import os
import jinja2
import cookielib
import urllib2

import requests

import datetime
import facebook
import jinja2
import os
import webapp2
import urllib2
from operator import itemgetter, attrgetter
from webapp2_extras import json


import facebook
import os.path
import wsgiref.handlers
import logging
import urllib2
import hashlib

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import fetch
 
import webapp2

from google.appengine.ext import db
from webapp2_extras import sessions

from google.appengine.api import lib_config
import logging

import sys
logging.getLogger().setLevel(logging.DEBUG)
reload(sys)
sys.setdefaultencoding('utf-8')

_config = lib_config.register('main', {'FACEBOOK_ID':None, 'FACEBOOK_SECRET':None})


FACEBOOK_APP_ID = _config.FACEBOOK_ID
FACEBOOK_APP_SECRET = _config.FACEBOOK_SECRET

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')


class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)


class BaseHandler(webapp2.RequestHandler):

    logging.info("BaseHandler 기본 핸들")

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
            logging.info("User is logged in.")
            return self.session.get("user")
        else:
            # To workaround "HTTPError: HTTP Error 400: Bad Request" 
            # in get_access_token_from_code() uncomment:
            #return None
            logging.info("Check if user is logged in to Facebook.")
            # Either used just logged in or just saw the first page
            # We'll see here
            cookie = facebook.get_user_from_cookie(self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Okay so user logged in.
                # Now, check to see if existing user
                user = User.get_by_key_name(cookie["uid"])
                logging.info("Cookie found, user is logged in.")
                if not user:
                    logging.info('New app user')
                    graph = facebook.GraphAPI(cookie["access_token"])

                    # replace with long live access token
                    token_full = graph.extend_access_token(app_id=FACEBOOK_APP_ID,app_secret=FACEBOOK_APP_SECRET)
                    token = token_full['access_token']
                    #logging.info('old token expires ' + cookie['expires'])
                    #logging.info('new token expires ' + token_full['expires'])
                    graph.access_token = token

                    # save user in objectstore
                    profile = graph.get_object("me")
                    user = User(
                        key_name=str(profile["id"]),
                        id=str(profile["id"]),
                        name=profile["name"],
                        profile_url=profile["link"],
                        access_token=token,
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


class HomeHandler(BaseHandler):
    def get(self):
        user = self.current_user
        locations = dict()
        friends_count = 0
        friends_count_2 = 0
        if user:
            graph = facebook.GraphAPI(user["access_token"])


        self.response.out.write(user);
        #return
        logging.info(1)
        #if self.current_user is None:
        #self.current_user

        if user:
            userprefs = models.get_userprefs(user["id"])
        else:
            userprefs = None
    
        if userprefs:
            current_location = userprefs.location_id

        locations_list = sorted(locations.items(), key=lambda l: l[1]['name'])
        
        template = jinja_environment.get_template('view/example.html')
        logging.info(_config.FACEBOOK_ID)
        logging.info(_config.FACEBOOK_SECRET)
        logging.info(2)
        logging.info(self.request.cookies)
            
        logging.info(self.current_user)
        
        self.response.out.write(template.render(dict(
            facebook_app_id=FACEBOOK_APP_ID,
            current_user=self.current_user
        )))
        logging.info(3)
        

    def post(self):
        url = self.request.get('url')
        file = urllib2.urlopen(url)
        graph = facebook.GraphAPI(self.current_user['access_token'])
        response = graph.put_photo(file, "Test Image")
        photo_url = ("http://www.facebook.com/"
                     "photo.php?fbid={0}".format(response['id']))
        self.redirect(str(photo_url))


class LogoutHandler(BaseHandler):
    def get(self):
        if self.current_user is not None:
            self.session['user'] = None

        self.redirect('/')

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__))
)

app = webapp2.WSGIApplication(
    [('/', HomeHandler), ('/logout', LogoutHandler)],
    debug=True,
    config=config
)