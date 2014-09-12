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
from time import strptime, strftime
        
import re, datetime

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
from google.appengine.api import memcache

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
        args = {}
        args['tags'] = self.tags()
        args['tag'] = tag
        template = JINJA_ENVIRONMENT.get_template('/view/home.html')
        self.response.write(template.render(args))


class FeedDataHandler(BaseHandler):
    def get(self, tag=None):
        from google.appengine.datastore.datastore_query import Cursor
        import json
        curs = Cursor(urlsafe=self.request.get('cursor'))
        feeds = []
        more = False
        next_curs = None
        ckey = 'FeedDataHandler.%s.%s' % (tag, self.request.get('cursor'))
        cdata = memcache.get(ckey)
        if cdata is not None:
            feeds, next_curs, more = cdata
        else:
            if tag == None or tag == 'None' : 
                feedRef, next_curs, more = Feed.query().order(-Feed.created_time).fetch_page(20, start_cursor = curs)
                for feed in feedRef:
                    feeds.append(feed.to_dict())
            else:
                tagRef = Tag.query(Tag.name == tag).get()
                if tagRef:
                    trRef, next_curs, more = TagRelation.query(TagRelation.tag == tagRef.key).order(-TagRelation.created_time).fetch_page(20, start_cursor = curs)
                    for row in trRef:
                        feed = row.feed.get();
                        feeds.append(feed.to_dict())
            if not memcache.add(ckey, (feeds, next_curs, more), 60*1):
                logging.error('Memcache set failed.')
        args = {}
        args['feeds'] = feeds;
        args['cursor'] = more and next_curs and  next_curs.urlsafe();
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
            
            fro_m = row.get('from')
            mem = Member.query(Member.source_id == fro_m['id']).get()
            if(mem):
                mem_key = mem.key
            else:
                mem = Member()
                mem.type = 1
                mem.name = fro_m['name']
                mem.source_id = fro_m['id']
                mem.source_type = 1
                mem_key = mem.put();
            if not mem_key:
                continue

            feed = Feed(
                source_id=row.get('id') or '',
                source_type=1,
                message=row.get('message') or '',
                full_picture=row.get('full_picture') or '',
                created_time=datetime.datetime.strptime(row.get('created_time') or '1970-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000'),
                updated_time=datetime.datetime.strptime(row.get('updated_time') or '1979-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000'),
                link=row.get('link') or '',
                member = mem_key
             )

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
        max_created_time = max_created_time.strftime('%Y-%m-%dT%H:%M:%S+0000')


        if config:
            config.value = max_created_time
            config.put()
        else:
            Config(key='last_synced_time', value=max_created_time).put()
        self.response.write(NewsFeedMessage + '<hr >')


def syncComment(_post):
    import datetime;
    graph = Graph()
    post = graph.post(_post.source_id)
    if 'comments' in post:
        pass
    else:
        return True;
    for com in post['comments']['data']:
        #todo last_comment_sync_time에 따라서 동기화 할 것인지 여부를 판단한다.
        created_time = datetime.datetime.strptime(com['created_time'] or '1970-01-01T00:00:00+0000','%Y-%m-%dT%H:%M:%S+0000')
        if _post.last_comment_sync_time and created_time <= _post.last_comment_sync_time:
            continue
        comObj = Comment()
        comObj.source_id = com['id']
        comObj.source_type = 1
        comObj.message = com['message']
        logging.info(comObj.message)
        comObj.created_time = created_time
        comObj.parent = _post.key
        mem = Member.query(Member.source_id == com['from']['id']).get()
        if(mem):
            mem_key = mem.key
        else:
            mem = Member()
            mem.name = com['from']['name']
            mem.source_id = com['from']['id']
            mem.source_type = 1
            mem_key = mem.put();    
        if not mem_key:
            continue
        comObj.member = mem_key
        comObj.put()
    _post.last_comment_sync_time = datetime.datetime.now()
    _post.put()
    return True

class MemberHandler(BaseHandler):
    def get(self, type):
        from google.appengine.datastore.datastore_query import Cursor
        import json
        args = {}
        args['tags'] = self.tags()
        curs = Cursor(urlsafe=self.request.get('cursor'))
        member_key = self.request.get('member')
        entries = []
        if type == 'post':
            entryRef, next_curs, more = Feed.query(Feed.member == ndb.Key(urlsafe = member_key)).order(-Feed.created_time).fetch_page(20, start_cursor = curs)
        else :
            entryRef, next_curs, more = Comment.query(Comment.member == ndb.Key(urlsafe = member_key)).order(-Comment.created_time).fetch_page(20, start_cursor = curs)
        for entry in entryRef:
            entries.append(entry.to_dict())
        args['entries'] = entries;
        args['cursor'] = more and next_curs and  next_curs.urlsafe();
        args['more'] = more;
        args['member_key'] = member_key;
        args['type'] = type;
        template = JINJA_ENVIRONMENT.get_template('/view/member.html')
        self.response.write(template.render(args))

class PostHandler(BaseHandler):
        def get(self, source_id):
            args = {}
            post = Feed.query(Feed.source_id ==  source_id).get()
            ckey = 'PostHandler.%s' % source_id
            cdata = memcache.get(ckey)
            if cdata is not None:
                args = cdata
            else:
                args['tags'] = self.tags()
                syncComment(post)
                _comments = Comment.query(Comment.parent == post.key).order(Comment.created_time).fetch()
                comments = []
                for comment in _comments:
                    comments.append(comment.to_dict())
                post_key = post.key.urlsafe()
                args['post'] = post.to_dict();
                args['post']['message'] = message(args['post']['message'])
                args['post']['member'] = post.member.get().to_dict()
                args['comments'] = comments;
                if not memcache.add(ckey, args, 60 * 10):
                    logging.error('Memcache set failed.')
            template = JINJA_ENVIRONMENT.get_template('/view/post.html')
            self.response.write(template.render(args))


class CommentDataHandler(BaseHandler):
    def get(self, post_key):
        from google.appengine.datastore.datastore_query import Cursor
        import json
        next_curs = Cursor(urlsafe=self.request.get('next_cursor'))
        logging.info(next_curs)
        entryRef, next_cursor, more = Comment.query(Comment.parent == ndb.Key(urlsafe = post_key)).order(Comment.created_time).fetch_page(4, start_cursor = next_curs)
        template = JINJA_ENVIRONMENT.get_template('/view/post.html')
        entries = []
        for _entry in entryRef:
            entry = _entry.to_dict()
            entry['member'] = _entry.member.get().to_dict()
            entries.append(entry)
        self.response.write(json.dumps({'entries':entries, 'next_cursor':next_cursor.urlsafe() if next_cursor else None, 'more':more}))

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
        logging.info(ndb.Key(urlsafe='ahZkZXZ-dm9jYWwtdGVybWluYWwtNjY2chMLEgZNZW1iZXIYgICAgIDSgQgM'))
        a = {'id':'egoing', 'local':'seoul'}
        
        if 'ida' in a:
            logging.info(a['id'])
        else:
            logging.info('test')
        return

        graph = Graph()
        content = graph.groups()
        fro_m = content['feed']['data'][0]['from']

        mem = Member()
        mem.type = 1
        mem.name = fro_m['name']
        mem.social_id = fro_m['id']
        mem.put();

        self.response.write("<strong>access token fail</strong>")       

app = webapp2.WSGIApplication(
    [
        ('/', HomeHandler),
        ('/feed', HomeHandler),
        ('/feed/(.+)', HomeHandler),
        ('/feeddata/(.+)', FeedDataHandler),
        ('/auth/logout', LogoutHandler),
        ("/auth/login", LoginHandler),
        ('/groups_api', GroupsGraphApiHandler),
        ('/post/(.+)', PostHandler),
        ('/member/(.+)', MemberHandler),
        ('/refresh_token', AccessTokenHandler), 
        ('/commentdata/(.+)', CommentDataHandler),
        ('/t', TestHandler)],
        debug=True
)
