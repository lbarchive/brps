# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2009  Yu-Jie Lin
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""For blogs"""

import logging
import sets
import simplejson as json
import urllib

from google.appengine.api import memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db

from brps import util
from brps.util import json_str_sanitize


# Blog cache time in seconds
BLOG_CACHE_TIME = 86400
# In seconds
UPDATE_INTERVAL = 86400 * 30


BASE_API_URI = 'http://www.blogger.com/feeds/'
BLOG_POSTS_FEED = BASE_API_URI + '%s/posts/default?v=2&alt=json&max-results=0'


class Blog(db.Model):
  """Blog data model"""
  blog_id = db.IntegerProperty()
  name = db.TextProperty()
  uri = db.TextProperty()
  last_updated = db.DateTimeProperty()
  last_reviewed = db.DateTimeProperty()
  blocked = db.BooleanProperty(default=False)


def get(blog_id):
  """Returns blog from memcache or datastore

  This method also updates if data is too old"""

  if blog_id:
    key_name = 'b%d' % blog_id
    b = memcache.get(key_name)
    if not b:
      b = Blog.get_by_key_name(key_name)
      if not b:
        return add(blog_id)
      memcache.add(key_name, b, BLOG_CACHE_TIME)
    # Check if need to update
    if util.td_seconds(b.last_updated) > UPDATE_INTERVAL:
      f = fetch(BLOG_POSTS_FEED % blog_id)
      if f.status_code == 200:
        p_json = json.loads(json_str_sanitize(f.content))
        blog_name = p_json['feed']['title']['$t'].strip()
        blog_uri = ''
        for link in p_json['feed']['link']:
          if link['rel'] == 'alternate' and link['type'] == 'text/html':
            blog_uri = link['href']
            break
      else:
        return None
      b = db.run_in_transaction(transaction_update_blog, blog_id, blog_name,
          blog_uri)
      memcache.set(key_name, b, BLOG_CACHE_TIME)
    return b
  return None


def add(blog_id):
  """Adds new blog to db"""
  logging.debug('Adding blog %d' % blog_id)
  key_name = 'b%d' % blog_id
  f = fetch(BLOG_POSTS_FEED % blog_id)
  if f.status_code == 200:
    p_json = json.loads(json_str_sanitize(f.content))
    blog_name = p_json['feed']['title']['$t'].strip()
    blog_uri = ''
    for link in p_json['feed']['link']:
      if link['rel'] == 'alternate' and link['type'] == 'text/html':
        blog_uri = link['href']
        break
  else:
    return None
  b = db.run_in_transaction(transaction_add_blog, blog_id, blog_name, blog_uri)
  memcache.set(key_name, b, BLOG_CACHE_TIME)
  return b


def reviewed(blog_id):
  '''Mark a blog as reviewed'''
  b = get(blog_id)
  if not b:
    return None

  b.last_reviewed = util.now()
  b.put()

  key_name = 'b%d' % blog_id
  memcache.set(key_name, b)


def block(blog_id):
  '''Mark a blog as reviewed'''
  b = get(blog_id)
  if not b:
    return None

  b.blocked = True
  b.put()

  key_name = 'b%d' % blog_id
  memcache.set(key_name, b)


def transaction_add_blog(blog_id, blog_name, blog_uri):
  """Transaction function to add a new blog"""
  b = Blog(key_name='b%d' % blog_id)
  b.blog_id = blog_id
  b.name = blog_name
  b.uri = blog_uri
  b.last_updated = util.now()
  b.put()
  return b


def transaction_update_blog(blog_id, blog_name, blog_uri):
  """Transaction function to update related posts of a post"""
  b = Post.get_by_key_name('b%dp%d' % (blog_id, post_id))
  b.last_updated = util.now()
  b.put()
  return b

