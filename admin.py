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

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class AdminHandler(BaseHandler):

    def get(self, tag=None):
        import json
        self.require_admin()
        args = {}
        conf = Configuration.query().get()
        if not conf:
            conf = Configuration()
        tagcRef = TagConfig.query().order(TagConfig.type,TagConfig.order).fetch()
        tagcs = [tag.to_dict() for tag in tagcRef]
        args['tagConfig'] = json.dumps(tagcs,indent=4, separators=(',', ': '), ensure_ascii=False).encode('utf8')
        args['configuration'] = json.dumps(conf.to_dict(), indent=4, separators=(',', ': '),ensure_ascii=False).encode('utf8')
        args['tags'] = self.tags();
        template = JINJA_ENVIRONMENT.get_template('/view/admin.html')
        self.response.write(template.render(args))

class TagHandler(BaseHandler):
    def post(self):
      import json
      old_tags = TagConfig.query().fetch()  
      old_tags_keys = [tag for tag in old_tags]
      new_tags = json.loads(self.request.get('tag'))
      for tag in new_tags:
        tagcRef = TagConfig()
        tagcRef.name = tag['name']
        tagcRef.type = tag['type'];
        tagcRef.order =tag['order'];
        tagcRef.put();
      for tag in old_tags_keys:
        tag.key.delete()
      self.redirect('/admin');

class ConfigurationHandler(BaseHandler):

    def post(self):
        conf = self.request.get('configuration')
        if conf:
            import json
            config = json.loads(conf)
            confRef = Configuration.query().get()
            if not confRef:
                confRef = Configuration()
            confRef.FACEBOOK_ID = config['FACEBOOK_ID']
            confRef.FACEBOOK_SECRET = config['FACEBOOK_SECRET']
            confRef.FACEBOOK_GROUP_ID = config['FACEBOOK_GROUP_ID']
            confRef.FEED_PAGE_SCALE = config['FEED_PAGE_SCALE']
            confRef.put()
            self.redirect('/admin')
        else:
            self.response.write('Something wrong')


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
        self.response.write(json.dumps({'result': True}))

config = {}
config['webapp2_extras.sessions'] = dict(secret_key='')
app = webapp2.WSGIApplication(
    [
        ('/admin', AdminHandler),
        ('/admin/reset', ResetHandler),
        ('/admin/login', FBLoginHandler),
        ('/admin/configuration', ConfigurationHandler),
        ('/admin/tag', TagHandler)
    ],
    debug=True,
    config=config
)
