#!/usr/bin/env python
# -*- coding:utf-8 -*-

import webapp2




import time

from google.appengine.api import lib_config

from model import *
from cookie import *


_config = lib_config.register(
    'main', {'FACEBOOK_ID': None, 'FACEBOOK_SECRET': None, 'FQL_ACCESS_TOKEN': None, 'GROUP_ID': None})

# 페이스북 앱 정보

FACEBOOK_APP_ID = _config.FACEBOOK_ID
FACEBOOK_SECRET = _config.FACEBOOK_SECRET
FQL_ACCESS_TOKEN = _config.FQL_ACCESS_TOKEN
GROUP_ID = _config.GROUP_ID



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

def parse_cookie(value):
    """Parses and verifies a cookie value from set_cookie"""
    if not value:
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    result = cookie_signature(FACEBOOK_SECRET, parts[0], parts[1]);
    logging.info(result);
    logging.info(parts[2]);
    if result != parts[2]:
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

