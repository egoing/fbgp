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

_config = lib_config.register('main', {})
print _config
JINJA_ENVIRONMENT = jinja2.Environment(
  loader = jinja2.FileSystemLoader(os.path.dirname(__file__)),
  extensions = ['jinja2.ext.autoescape'])

class MainHandler(webapp2.RequestHandler):
    def get(self):
    	graph = facebook.GraphAPI('CAACEdEose0cBAOhdepYMr1cSkhHwCQbZC2K7BEB2VaUfXusmg85zqOXVQ5Kgm5qC1BMkZAZCQB7nRxzMlXMr49IP0G9yv32vbvGl2xld8QLAAqWm0erMFHj9Ya7ez1X5iEfHL77Tkedm3YmO3IpGJoGIwpbkiqLKIJo8vP4iVGv6adb2WdDyBYTwFMZCKugqV0nXZBvoZCzCKv26OFUF2SPcnFowZCtTpUZD')
        obj = graph.get_object("me")
        logging.info(obj);
        
        #logging.info(group)
        self.response.write('Hello world!')
        
        template = JINJA_ENVIRONMENT.get_template('view/base.html');
        self.response.out.write(template.render());

app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)