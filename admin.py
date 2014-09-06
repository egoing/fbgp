#!/usr/bin/env python
# -*- coding:utf-8 -*-
import webapp2
import jinja2
import os
import logging
import model
import facebook
from google.appengine.api import lib_config
from google.appengine.ext import ndb
from webapp2_extras import sessions
from google.appengine.api import users
from facebook import Graph
from controller import *

# 템플릿 프레임워크 환경 설정
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'])

class AdminHandler(BaseHandler):
    def get(self, tag=None):
        self.require_admin()
        args = {}
        template = JINJA_ENVIRONMENT.get_template('/view/admin.html')
        self.response.write(template.render(args))

class FBLoginHandler(BaseHandler):
    def get(self):
        graph = Graph()
        graph.login(self)


class ResetHandler(BaseHandler):
    def get(self):
        self.require_admin()
        import json
        ndb.delete_multi(Tag.query().fetch(keys_only=True))
        ndb.delete_multi(Config.query().fetch(keys_only=True))
        ndb.delete_multi(TagRelation.query().fetch(keys_only=True))
        ndb.delete_multi(User.query().fetch(keys_only=True))
        ndb.delete_multi(Feed.query().fetch(keys_only=True))
        ndb.delete_multi(Comment.query().fetch(keys_only=True))
        ndb.delete_multi(Member.query().fetch(keys_only=True))
        self.response.write(json.dumps({'result':True}))

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')
app = webapp2.WSGIApplication(
    [
    ('/admin', AdminHandler),
    ('/admin/reset', ResetHandler),
    ('/admin/login', FBLoginHandler)
    ],
    debug=True,
    config=config
)