#!/usr/bin/env python
# -*- coding:utf-8 -*-

from google.appengine.ext import ndb

# dao 모델 설정

#source_type : 1. 페이스북
#source_id : source_type에서 사용하는 id

DATE_FORMAT = '%y-%m-%d %H:%M'

class User(ndb.Model):
    id = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)
    name = ndb.StringProperty(required=True)
    profile_url = ndb.StringProperty(required=True)
    access_token = ndb.StringProperty(required=True)

class Configuration(ndb.Model):
    FACEBOOK_ID = ndb.StringProperty(required=True)
    FACEBOOK_SECRET = ndb.StringProperty(required=True)
    FACEBOOK_GROUP_ID = ndb.StringProperty(required=True)
    FEED_PAGE_SCALE = ndb.StringProperty(required=True)

class TagConfig(ndb.Model):
    name = ndb.StringProperty(required=True)
    order = ndb.IntegerProperty(required=True)
    type = ndb.IntegerProperty(required=True)

class Config(ndb.Model):
    key = ndb.StringProperty(required=True)
    value = ndb.TextProperty(required=True)

class Member(ndb.Model):
    # 1. facebook
    source_type = ndb.IntegerProperty(required=True)
    source_id = ndb.StringProperty(required=True)
    name = ndb.TextProperty(required=True)

    def to_dict(self):
        obj = {}
        obj['source_type'] = self.source_type;
        obj['source_id'] = self.source_id;
        obj['name'] = self.name;
        obj['key_urlsafe'] = self.key.urlsafe()
        return obj;
    
class Feed(ndb.Model):
    source_id = ndb.StringProperty(required=True)
    source_type = ndb.IntegerProperty(required=True)
    message = ndb.TextProperty(required=True)
    full_picture = ndb.StringProperty()
    created_time = ndb.DateTimeProperty(required=True)
    updated_time = ndb.DateTimeProperty(required=True)
    link = ndb.StringProperty()
    last_comment_sync_time = ndb.DateTimeProperty()
    member = ndb.KeyProperty(kind=Member, required=True)
    
    def to_dict(self):
        from pytz.gae import pytz
        user_tz  = pytz.timezone('Asia/Seoul')
        obj = {}
        obj['message'] = self.message
        obj['created_time'] = self.created_time.replace(tzinfo=pytz.utc).astimezone(user_tz).strftime(DATE_FORMAT);
        obj['updated_time'] = self.created_time.replace(tzinfo=pytz.utc).astimezone(user_tz).strftime(DATE_FORMAT);
        obj['source_id'] = self.source_id
        obj['source_type'] = self.source_type
        obj['full_picture'] = self.full_picture
        obj['member'] = self.member.get().to_dict()
        obj['key_urlsafe'] = self.key.urlsafe()
        return obj;

class Comment(ndb.Model):
    source_id = ndb.StringProperty(required=True)
    source_type = ndb.IntegerProperty(required=True)
    message = ndb.TextProperty(required=True)
    created_time = ndb.DateTimeProperty()
    parent = ndb.KeyProperty(kind=Feed, required=True)
    member = ndb.KeyProperty(kind=Member, required=True)

    def to_dict(self):
        from pytz.gae import pytz
        user_tz  = pytz.timezone('Asia/Seoul')
        obj = {}
        obj['source_id'] = self.source_id
        obj['source_type'] = self.source_type
        obj['message'] = self.message
        obj['created_time'] = self.created_time.replace(tzinfo=pytz.utc).astimezone(user_tz).strftime(DATE_FORMAT);
        obj['parent'] = self.parent.urlsafe()
        obj['member'] = self.member.urlsafe()
        obj['key_urlsafe'] = self.key.urlsafe()
        return obj;

    
class Tag(ndb.Model):
    name = ndb.StringProperty(required=True)
    official = ndb.BooleanProperty(required=True, default=False)

class TagRelation(ndb.Model):
    feed = ndb.KeyProperty(kind=Feed, required=True)
    tag = ndb.KeyProperty(kind=Tag, required=True)
    created_time = ndb.DateTimeProperty(required=True)
