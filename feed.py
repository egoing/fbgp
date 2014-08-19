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
import facebook

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
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import time
import re

from webapp2_extras import sessions

from google.appengine.api import lib_config

import logging

import sys
logging.getLogger().setLevel(logging.DEBUG)
reload(sys)
sys.setdefaultencoding('utf-8')

_config = lib_config.register('main', {'FACEBOOK_ID':None, 'FACEBOOK_SECRET':None, 'FQL_ACCESS_TOKEN':None, 'GROUP_ID':None})

#페이스북 앱 정보

FACEBOOK_APP_ID = _config.FACEBOOK_ID
FACEBOOK_APP_SECRET = _config.FACEBOOK_SECRET
FQL_ACCESS_TOKEN = _config.FQL_ACCESS_TOKEN
GROUP_ID = _config.GROUP_ID

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')


# dao 모델 설정
class User(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)

#템플릿 프레임워크 환경 설정

JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions = ['jinja2.ext.autoescape'])

class BaseHandler(webapp.RequestHandler):
    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected.
        페이스북 유저가 로그인되어 있으면 페이스북 객체를 리턴한고 그렇지 않은면 None를 리턴함
        """
        logging.info("순서 1")
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = User.get_by_key_name(user_id)
        return self._current_user



#메인 클래스
class HomeHandler(BaseHandler):
    def get(self):
        logging.info("순서 먼저 호")
        args = dict(current_user=self.current_user)
        template = JINJA_ENVIRONMENT.get_template('/view/oauth.html')
        self.response.write(template.render(args))


#로그인 담당
class LoginHandler(BaseHandler):
    def get(self):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID,
                    redirect_uri=self.request.path_url)
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")
            response = cgi.parse_qs(urllib.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            #엑시스 토근을 요청
            access_token = response["access_token"][-1]

            # Download the user profile 사용자 프로파이일을 다운로드하고 
            # and cache a local instance of the 로컬 DAO에 프로필정보를 담는다.
            # basic profile info
            profile = json.load(urllib.urlopen("https://graph.facebook.com/me?" + urllib.urlencode(dict(access_token=access_token))))
            
            #logging.info(urllib.urlencode("debeg" + urllib.urlencode(dict(access_token=access_token)))
            
            logging.info("https://graph.facebook.com/me?" + urllib.urlencode(dict(access_token=access_token)))


            logging.info("after call profile ")
            user = User(key_name=str(profile["id"]), id=str(profile["id"]),
                        name=profile["name"], access_token=access_token,
                        profile_url=profile["link"])
            user.put()
            set_cookie(self.response, "fb_user", str(profile["id"]), expires=time.time() + 30 * 86400)
            self.redirect("/")
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(args))


class LogoutHandler(BaseHandler):
    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/")


"""그룹에 글을 가져온다. FQL를 이용한다. FQL은 페이스북 API v2.1에서 디플리케션 되었다. 신규로 등록된 어플리케이션 그 이전 버전의 API를 사용하지 못한다.
자세한 정보 : 
1. http://stackoverflow.com/questions/25256428/query-facebook-for-what-version-of-the-graph-api-is-being-used-can-be-used
2. https://developers.facebook.com/docs/apps/changelog
"""
class GroupsFqlHandler(BaseHandler):
    def get(self):
        user = self.current_user
        self.response.write("fql groups post")
        self.response.write(user.name)
        if user:
            query = "SELECT post_id FROM stream WHERE source_id='"+ GROUP_ID +"' LIMIT 10"
            fql = {'q': "SELECT post_id FROM stream WHERE source_id='"+ GROUP_ID +"' LIMIT 10"}
            fql1 = {'q': "SELECT message, message_tags FROM stream WHERE source_id='1389107971348349' LIMIT 10"}

            args = "https://graph.facebook.com/v2.0/fql?access_token=" + FQL_ACCESS_TOKEN + "&" +urllib.urlencode(fql1) +"&format=json"
            #logging.info(args)
            file = urllib2.urlopen(args, None, timeout=5000)

            import unicodedata

            try:
                content = file.read()
                #logging.info(content)
                self.response.write(" <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" /><br />")

                stringUnicode = '\ud504\ub85c\uadf8\ub798\ubc0d\uacfc'
                uni = stringUnicode.decode("UTF-8")
                self.response.write('<script>'+'console.log(unescape("'+uni.encode('utf-8')+'"))</script>')
                self.response.write('<script>'+'document.write(unescape("'+uni.encode('utf-8')+'"))</script>')
                self.response.write(uni.replace('%u',r'\u').decode("unicode_escape"))    
            except Exception, e:
                raise e
            finally:
                file.close()
        else:
            self.response.write("2")


class GroupsGraphApiHandler(BaseHandler):
    def get(self) :
        
        #iself.response.write("groupsGraphAPI Call")
        user = self.current_user
        if user:
            logging.info("verify access_token")
            logging.info(user.access_token)
            token=user.access_token

            graphApi = "https://graph.facebook.com/" + GROUP_ID + "?fields=feed.limit(100)&method=GET&format=json&suppress_http_code=1&access_token=" + str(token)
            logging.info(graphApi)
            file = urllib2.urlopen(graphApi)
            content = json.loads(file.read())

            #에러 처리
            if "error" in content:
                if content["error"]["code"] == 613:
                    time.sleep(200)
                    file = urllib2.urlopen("https://graph.facebook.com/" + GROUP_ID + "?fields=feed&method=GET&format=json&suppress_http_code=1&access_token=" + str(token))
                    content = json.loads(file.read())

            previous = content["feed"]["paging"]["next"]
            NewsFeed = content["feed"]

            logging.info("previous : " + previous)

        NewsFeedMessage = '<b>message</b>'


        for x in range(0, len(content["feed"]["data"])):
            NewsFeedMessage +=  '<hr />' +content["feed"]["data"][x]["message"]
            content["feed"]["data"][x]["message"]
            
        self.response.write(NewsFeedMessage+'<hr >')

        #self.response.write(NewsFeedData.replace('%u',r'\u').decode("unicode_escape"))    
      

def safe_str(obj):
    """ return the byte string representation of obj """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')


def set_cookie(response, name, value, domain=None, path="/",expires=None):
    """Generates and signs a cookie for the give name/value
    승인된 쿠키를 생
    """
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain:
        cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(
            expires, localtime=False, usegmt=True)
    header_value = cookie.output()[12:]
    response.headers.add_header("Set-Cookie", header_value)


def parse_cookie_simple(value):
    if not value:
        return None

    return base64.b64decode(value)


def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value:
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None


def cookie_signature(*parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    hash = hmac.new(FACEBOOK_APP_SECRET, digestmod=hashlib.sha1)
    for part in parts:
        hash.update(part)
    return hash.hexdigest()


app = webapp2.WSGIApplication(
    [('/', HomeHandler), ('/auth/logout', LogoutHandler), ("/auth/login", LoginHandler), ('/groups', GroupsFqlHandler), ('/groups_api', GroupsGraphApiHandler)],
    debug=True,
    config=config
)
