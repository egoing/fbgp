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


from facebook import Graph
from controller import *
from helper import *

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

    def get(self, tag=None):
        if self.current_user:
            args = dict(current_user=self.current_user)
        else:
            args = {}
        if tag:
            tagRef = Tag.query(Tag.name == tag).get()
            if not tagRef:
                template = JINJA_ENVIRONMENT.get_template('/view/nodata.html')
                return
            trRef = TagRelation.query(TagRelation.tag == tagRef.key).fetch()
            args['feeds'] = []
            for x in trRef:
                args['feeds'].append(x.feed.get())
        else:
            args['feeds'] = Feed.query().fetch()
        args['tags'] = Tag.query().fetch()
        args['tag'] = tag
        template = JINJA_ENVIRONMENT.get_template('/view/home.html')
        self.response.write(template.render(args))


class FeedDataHandler(BaseHandler):
    def _content_pretty(self, input):
        return autolink(input.replace('\n', '<br />'))
    def _objectfy(self, feed):
        obj = {}
        obj['message'] = self._content_pretty(feed.message)
        obj['created_time'] = feed.created_time.strftime('%Y-%m-%dT%H:%M:%S+0000');
        obj['updated_time'] = feed.updated_time.strftime('%Y-%m-%dT%H:%M:%S+0000');
        obj['id'] = feed.id
        obj['full_picture'] = feed.full_picture
        return obj;
    def post(self, tag=None, cursor=None):
        from google.appengine.datastore.datastore_query import Cursor
        import json
        curs = Cursor(urlsafe=self.request.get('cursor'))
        feeds = []
        if tag == None or tag == 'None' : 
            feedRef, next_curs, more = Feed.query().fetch_page(20, start_cursor = curs)
            for feed in feedRef:
                feeds.append(self._objectfy(feed))
        else:
            tagRef = Tag.query(Tag.name == tag).get()
            trRef, next_curs, more = TagRelation.query(TagRelation.tag == tagRef.key).fetch_page(20, start_cursor = curs)
            for row in trRef:
                feed = row.feed.get();
                feeds.append(self._objectfy(feed))
        args = {}
        args['feeds'] = feeds;
        args['cursor'] = next_curs.urlsafe();
        args['more'] = more;
        self.response.write(json.dumps(args))
        pass


# 로그인 담당
class LoginHandler(BaseHandler):

    def get(self):
        graph = Graph()
        result = graph.login(self)
        if not result:
            self.redirect("/")
        else:
            self.redirect(
                "https://graph.facebook.com/oauth/authorize?" + urllib.urlencode(result))


class LogoutHandler(BaseHandler):

    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/")


class GroupsGraphApiHandler(BaseHandler):

    def get(self):
        from time import strptime, strftime
        import re, datetime
        graph = Graph()
        content = graph.groups()
        
        previous = content["feed"]["paging"]["next"]
        NewsFeed = content["feed"]

        NewsFeedMessage = '<b>message</b>'
        config = Config.query(Config.key == 'last_synced_time').get()
        if config:
            last_synced_time = datetime.datetime.strptime(config.value,'%Y-%m-%dT%H:%M:%S+0000')
        else:
            last_synced_time = datetime.datetime.strptime('1979','%Y')

        max_created_time = last_synced_time
        for row in content["feed"]["data"]:
            entry_created_time = datetime.datetime.strptime(row.get('created_time') or '1970-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000')
            if last_synced_time >= entry_created_time:
                continue

            NewsFeedMessage += '<hr />' + (row.get('message') or '')
            logging.info(datetime.datetime.strptime(row.get('created_time') or '1970-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000'))

            feed = Feed(
                id=row.get('id') or '',
                message=row.get('message') or '',
                full_picture=row.get('full_picture') or '',
                created_time=datetime.datetime.strptime(row.get('created_time') or '1970-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000'),
                updated_time=datetime.datetime.strptime(row.get('updated_time') or '1979-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000'),
                link=row.get('link') or '')

            feedKey = feed.put()
            p = re.compile(ur'#.+?(?=\s|$)')
            tags = re.findall(p, row.get('message') or '')
            for tag in tags:
                tag = tag.lower()[1:]
                tagRef = Tag.query(Tag.name == tag).get()
                if tagRef:
                    tagKey = tagRef.key
                else:
                    tagKey = Tag(name=tag, official=False).put()
                trRef = TagRelation()
                trRef.tag = tagKey
                trRef.feed = feedKey
                trRef.created_time = datetime.datetime.strptime(row['created_time'],'%Y-%m-%dT%H:%M:%S+0000')
                trRef.put()
            max_created_time = max(max_created_time, entry_created_time)
        logging.info(type(max_created_time))
        max_created_time = max_created_time.strftime('%Y-%m-%dT%H:%M:%S+0000')
        if config:
            config.value = max_created_time
            config.put()
        else:
            Config(key='last_synced_time', value=max_created_time).put()
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
        tag = '#java'
        tagRefGet = Tag.query().get()
        tagRefPut = Tag(name=tag).put()
        return
        tagRef = Tag.query(Tag.name == "#Java").get()
        if not tagRef:
            tagRef = Tag(name=tag.lower(), official=False).put()
        TagRelation(feed=feedRef, tag=tagRef).put()

app = webapp2.WSGIApplication(
    [
        ('/', HomeHandler),
        ('/feed', HomeHandler),
        ('/feed/(.+)', HomeHandler),
        ('/feeddata/(.+)/(.?)', FeedDataHandler),
        ('/auth/logout', LogoutHandler),
        ("/auth/login", LoginHandler),
        ('/groups_api', GroupsGraphApiHandler),
        ('/refresh_token', AccessTokenHandler, ('/t', TestHandler))],
        debug=True
)
