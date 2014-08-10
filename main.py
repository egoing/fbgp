#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2
import jinja2, os
import urllib2
import facebook
import logging
from google.appengine.api import lib_config

_config = lib_config.register('main', {'FACEBOOK_ID':None, 'FACEBOOK_SECRECT':None})

JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions = ['jinja2.ext.autoescape'])

class MainHandler(webapp2.RequestHandler):
    global _config
    def get(self):
    	template = JINJA_ENVIRONMENT.get_template('view/base.html')
        self.response.out.write(template.render(dict(
            facebook_app_id=_config.FACEBOOK_ID
            #,
            #current_user=self.current_user
        )))

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)