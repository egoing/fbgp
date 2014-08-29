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

import os


import urllib
import urllib2
import wsgiref.handlers

import json
from cookie import *


from google.appengine.ext import ndb
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import time
import re

from webapp2_extras import sessions

from google.appengine.api import lib_config

import logging

import sys
from model import *

logging.getLogger().setLevel(logging.DEBUG)
reload(sys)
sys.setdefaultencoding('utf-8')


_config = lib_config.register(
    'main', {'FACEBOOK_ID': None, 'FACEBOOK_SECRET': None, 'FQL_ACCESS_TOKEN': None, 'GROUP_ID': None, 'FEED_PAGE_SCALE' : 10})

# 페이스북 앱 정보

FACEBOOK_APP_ID = _config.FACEBOOK_ID
FACEBOOK_SECRET = _config.FACEBOOK_SECRET
FQL_ACCESS_TOKEN = _config.FQL_ACCESS_TOKEN
GROUP_ID = _config.GROUP_ID
FEED_PAGE_SCALE = _config.FEED_PAGE_SCALE


class Graph(object):

    def login(self, webapp2_obj):
            
            # Download the user profile 사용자 프로파이일을 다운로드하고
            # and cache a local instance of the 로컬 DAO에 프로필정보를 담는다.
            # basic profile info
        result = self.refreshToken(webapp2_obj);
        if result:
            return False
        else:
            args = dict(client_id=FACEBOOK_APP_ID,
                    redirect_uri=webapp2_obj.request.path_url)
            return args

    def refreshToken(self, webapp2_obj):    
       
        verification_code = webapp2_obj.request.get('code')
        args = dict(client_id=FACEBOOK_APP_ID,
                    redirect_uri=webapp2_obj.request.path_url)
        if verification_code:
            try:
                args["client_secret"] = FACEBOOK_SECRET
                args["code"] = verification_code
                response = cgi.parse_qs(urllib.urlopen(
                    "https://graph.facebook.com/oauth/access_token?" +
                    urllib.urlencode(args)).read())
                # 엑시스 토근을 요청
                access_token = response["access_token"][-1]
                profile = json.load( urllib.urlopen("https://graph.facebook.com/me?" + urllib.urlencode(dict(access_token=access_token))))

                user = User(
                            id=str(profile["id"]),
                            name=profile["name"], 
                            access_token=access_token,
                            profile_url=profile["link"])
                user.put()
                set_cookie(webapp2_obj.response, "fb_user", str( profile["id"]), expires=time.time() + 30 * 86400)
                return True
            except Exception, e:
                '''
                에러 로그 기록 , into db or file
                '''
                return False
            else:
                pass
            finally:
                pass
        else:
            webapp2_obj.redirect(
                "https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(args))


    def callFacebookAPI(self, graphAPI):

        file = urllib2.urlopen(graphAPI)
        return json.loads(file.read())



    def groups(self):

        graphApi = "https://graph.facebook.com/" + GROUP_ID + \
            "?fields=feed.limit("+str(FEED_PAGE_SCALE)+"){message,full_picture,created_time,updated_time,id,link}&method=GET&format=json&suppress_http_code=1&access_token=" + str(
                User.query().get().access_token)

        return self.callFacebookAPI(graphApi)

        # 에러 처리
        if "error" in content:
            if content["error"]["code"] == 613:
                time.sleep(200)
                return self.callFacebookAPI(graphApi)



    
    '''
    def post(self)
        url = "https://graph.facebook.com/" 
        return json.loads(file.read())


    '''

"""그룹에 글을 가져온다. FQL를 이용한다. FQL은 페이스북 API v2.1에서 디플리케션 되었다. 신규로 등록된 어플리케이션 그 이전 버전의 API를 사용하지 못한다.
자세한 정보 : 
1. http://stackoverflow.com/questions/25256428/query-facebook-for-what-version-of-the-graph-api-is-being-used-can-be-used
2. https://developers.facebook.com/docs/apps/changelog

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
                #uni = stringUnicode.decode("UTF-8")
                self.response.write('<script>'+'console.log(unescape("'+uni.encode('utf-8')+'"))</script>')
                self.response.write('<script>'+'document.write(unescape("'+uni.encode('utf-8')+'"))</script>')
                self.response.write(uni.replace('%u',r'\u').decode("unicode_escape"))    
            except Exception, e:
                raise e
            finally:
                file.close()
        else:
            self.response.write("2")

"""
