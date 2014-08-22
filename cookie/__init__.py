#!/usr/bin/env python
# -*- coding:utf-8 -*-
from google.appengine.api import lib_config
import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time


_config = lib_config.register('main', {'FACEBOOK_SECRET': None})
FACEBOOK_SECRET = _config.FACEBOOK_SECRET

def set_cookie(response, name, value, domain=None, path="/", expires=None):
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

def cookie_signature(*parts):
    """Generates a cookie signature.

    We use the Facebook app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    hash = hmac.new(FACEBOOK_SECRET, digestmod=hashlib.sha1)
    for part in parts:
        hash.update(part)
    return hash.hexdigest()

def parse_cookie_simple(value):
    if not value:
        return None

    return base64.b64decode(value)
