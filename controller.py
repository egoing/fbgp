#!/usr/bin/env python
# -*- coding:utf-8 -*-

import webapp2




import time

from google.appengine.api import lib_config

from model import *
from cookie import *
from google.appengine.api import users


_config = lib_config.register(
    'main', {'FACEBOOK_ID': None, 'FACEBOOK_SECRET': None, 'FQL_ACCESS_TOKEN': None, 'GROUP_ID': None})

# 페이스북 앱 정보

FACEBOOK_APP_ID = _config.FACEBOOK_ID
FACEBOOK_SECRET = _config.FACEBOOK_SECRET
FQL_ACCESS_TOKEN = _config.FQL_ACCESS_TOKEN
GROUP_ID = _config.GROUP_ID

CACHE_POST_IN_HOME = 60*20;
CACHE_COMMENT_IN_POST_TIME = 60*20
CACEH_POST_IN_PERMLINK = 60*60;

FEED_PAGE_SCALE = 50;
COMMEMT_PAGE_SCALE = 50;
SYNC_FEED_YESTERDAY_PAGE = 5;

class BaseHandler(webapp2.RequestHandler):

    @property
    def current_user(self):
        """Returns the logged in Facebook user, or None if unconnected.
        페이스북 유저가 로그인되어 있으면 페이스북 객체를 리턴한고 그렇지 않은면 None를 리턴함
        """
        if not hasattr(self, "_current_user"):
            self._current_user = None
            user_id = parse_cookie(self.request.cookies.get("fb_user"))
            if user_id:
                self._current_user = User.get_by_id(user_id)
        return self._current_user

    def require_admin(self):
        user = users.get_current_user()
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

    def tags(self):
        return TagConfig.query().order(TagConfig.type, TagConfig.order).fetch()

        

def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value:
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        return None
    timestamp = int(parts[1])
    if timestamp < time.time() - 30 * 86400:
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None
