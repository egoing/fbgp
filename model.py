#!/usr/bin/env python
# -*- coding:utf-8 -*-

from google.appengine.ext import ndb

# dao 모델 설정
class User(ndb.Model):
    id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    profile_url = ndb.StringProperty(required=True)
    access_token = ndb.StringProperty(required=True)

class Config(ndb.Model):
    key = ndb.StringProperty(required=True)
    value = ndb.TextProperty(required=True)

class Feed(ndb.Model):
    id = ndb.StringProperty(required=True)
    message = ndb.TextProperty(required=True)
    full_picture = ndb.StringProperty()
    created_time = ndb.StringProperty(required=True)
    updated_time = ndb.StringProperty(required=True)
    link = ndb.StringProperty()

class Tag(ndb.Model):
    name = ndb.StringProperty(required=True)
    official = ndb.BooleanProperty(required=True, default=False)

class TagRelation(ndb.Model):
    feed = ndb.KeyProperty(kind=Feed)
    tag = ndb.KeyProperty(kind=Tag)