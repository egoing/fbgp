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
    feed.py
    ~~~~~~~~~~~~

    Implements the facebook group post related objects.

    :copyright: (c) 2014 by DURU.
    :license: 
"""

"""A barebones AppEngine application that uses Facebook for login.

This application uses OAuth 2.0 directly rather than relying on Facebook's
JavaScript SDK for login. It also accesses the Facebook Graph API directly
rather than using the Python SDK. It is designed to illustrate how easy
it is to use the Facebook Platform without any third party code.

See the "appengine" directory for an example using the JavaScript SDK.
Using JavaScript is recommended if it is feasible for your application,
as it handles some complex authentication states that can only be detected
in client-side code.
"""
from facebook import Graph
from controller import *

import webapp2
import jinja2
import os

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
import urllib2
import wsgiref.handlers

import json
#from django.utils import simplejson as json
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from model import *
from cookie import *



import time
import re

from webapp2_extras import sessions

from google.appengine.api import lib_config

import logging



# 템플릿 프레임워크 환경 설정
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

# 메인 클래스


class HomeHandler(BaseHandler):

    def get(self):
        logging.info("순서 먼저 호")

        if self.current_user :
            args = dict(current_user=self.current_user)
        else:
            args = {}
        args['feeds'] = Feed.query().fetch()
        template = JINJA_ENVIRONMENT.get_template('/view/home.html')
        self.response.write(template.render(args))


# 로그인 담당
class LoginHandler(BaseHandler):

    def get(self):
        graph = Graph()
        result = graph.login(self)
        if not result:
            self.redirect("/")
        else:
            self.redirect("https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(result))


class LogoutHandler(BaseHandler):

    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/")


class GroupsGraphApiHandler(BaseHandler):

    def get(self):
        from time import strptime, strftime
        graph = Graph()
        content = graph.groups()

        previous = content["feed"]["paging"]["next"]
        NewsFeed = content["feed"]

        logging.info("previous : " + previous)

        NewsFeedMessage = '<b>message</b>'
        config = Config.query(Config.key == 'last_synced_time').get()
        if config:
            last_synced_time = strptime(config.value, "%Y-%m-%dT%H:%M:%S+0000")
        else:
            last_synced_time = strptime("1979", "%Y")

        max_created_time = last_synced_time

        for row in content["feed"]["data"]:
            entry_created_time = strptime(
                row['created_time'], "%Y-%m-%dT%H:%M:%S+0000")
            logging.info(last_synced_time)
            logging.info(entry_created_time)
            logging.info(last_synced_time >= entry_created_time)
            if last_synced_time >= entry_created_time:
                logging.info('skip')
                continue
            NewsFeedMessage += '<hr />' + row["message"]
            feed = Feed(
                id=row.get('id') or '',
                message=row.get('message') or '',
                full_picture=row.get('full_picture') or '',
                created_time=row['created_time'],
                updated_time=row['updated_time'],
                link=row.get('link') or '')
            feed.put()
            max_created_time = max(max_created_time, entry_created_time)
        if config:
            config.value = strftime("%Y-%m-%dT%H:%M:%S+0000", max_created_time)
            config.put()
        else:
            Config(key='last_synced_time', value=strftime(
                "%Y-%m-%dT%H:%M:%S+0000", max_created_time)).put()
        self.response.write(NewsFeedMessage + '<hr >')


class AccessTokenHandler(BaseHandler):

    def get(self):
        self.response.write("access token refresh")

        graph = Graph()
        if graph.refreshToken(self):
            self.response.write("<strong>access token issue</strong>")
        else:
            self.response.write("<strong>access token fail</strong>")    

        

class TestHandler(BaseHandler):

    def get(self):
        from time import strptime
        a = strptime('2002', '%Y')
        b = strptime('2011', '%Y')
        logging.info(max(a, b))
        return
        config = Config.query().get()
        if config:
            logging.info(config)
        else:
            Config(synced_time='8888').put()


app = webapp2.WSGIApplication(
    [('/', HomeHandler), ('/auth/logout', LogoutHandler), ("/auth/login", LoginHandler),
     ('/groups_api', GroupsGraphApiHandler), ('/t', TestHandler), ('/refresh_token', AccessTokenHandler)],
    debug=True
)
