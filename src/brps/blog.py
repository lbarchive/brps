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
import logging
import sets
import simplejson as json
import urllib
import md5
from google.appengine.api import memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db

from brps import util
from brps.util import json_str_sanitize
import config


# Blog cache time in seconds
BLOG_CACHE_TIME = 86400
# In seconds
UPDATE_INTERVAL = 86400 * 30


BASE_API_URI = 'http://www.blogger.com/feeds/'
BLOG_POSTS_FEED = BASE_API_URI + '%s/posts/summary?v=2&alt=json&max-results=%d'


class DbBlogReadOnly(Exception):

  pass


class InvalidBlogKeyError(Exception):

  pass


class Blog(db.Model):
  """Blog data model"""
  blog_id = db.IntegerProperty()
  name = db.TextProperty()
  uri = db.TextProperty()
  last_updated = db.DateTimeProperty()
  last_reviewed = db.DateTimeProperty(default=None)
  accepted = db.BooleanProperty(default=None)


def get_blog_name_uri(blog_id, max_results=0):

  f = fetch(BLOG_POSTS_FEED % (blog_id, max_results))
  if f.status_code == 200:
    p_json = json.loads(json_str_sanitize(f.content))
    blog_name = p_json['feed']['title']['$t'].strip()
    blog_uri = ''
    for link in p_json['feed']['link']:
      if link['rel'] == 'alternate' and link['type'] == 'text/html':
        blog_uri = link['href']
        if max_results:
          return (blog_name, blog_uri, len(p_json['feed']['entry']))
        else:
          return (blog_name, blog_uri, 0)
  logging.warning('Unable to retrieve blog name and uri: %s' % blog_id)
  return None


def get_blog_key(blog_id):
  blog_id = int(blog_id)
  key = memcache.get('k%d' % blog_id)
  if key:
    return key
  key = md5.md5('%d%s' % (blog_id, config.KEY_SALT)).hexdigest()[:8]
  memcache.set('k%d' % blog_id, key, 3600)
  return key


def get(blog_id, key=''):
  """Returns blog from memcache or datastore

  This method also updates if data is too old"""

  if blog_id:
    key_name = 'b%d' % blog_id
    b = memcache.get(key_name)
    if not b:
      b = Blog.get_by_key_name(key_name)
      if not b:
        if key != get_blog_key(blog_id):
          raise InvalidBlogKeyError('The key is invalid.')
        return add(blog_id)
      memcache.add(key_name, b, BLOG_CACHE_TIME)
    # Check if need to update
    if util.td_seconds(b.last_updated) > UPDATE_INTERVAL:
      b_nu = get_blog_name_uri(blog_id)
      # If couldn't get an updated name and uri, then return old b from cache
      # or data store.
      if b_nu:
        b = db.run_in_transaction(transaction_update_blog, blog_id, b_nu[0],
            b_nu[1])
        memcache.set(key_name, b, BLOG_CACHE_TIME)
    return b
  return None


def can_write():
  '''A helper function to ensure DB is not readonly'''
  if config.DB_WRITE and config.DB_BLOG_WRITE:
    return
  raise DbBlogReadOnly()


def add(blog_id):
  """Adds new blog to db"""
  can_write()

  logging.debug('Adding blog %d' % blog_id)
  key_name = 'b%d' % blog_id
  b_nu = get_blog_name_uri(blog_id, config.BLOG_MIN_POSTS)
  if b_nu:
    blocked = True if b_nu[2] < config.BLOG_MIN_POSTS else False
    b = db.run_in_transaction(transaction_add_blog, blog_id, b_nu[0], b_nu[1], blocked)
    memcache.set(key_name, b, BLOG_CACHE_TIME)
    return b
  return None


def reviewed(blog_id):
  '''Mark a blog as reviewed'''
  can_write()

  b = get(blog_id)
  if not b:
    return None

  b.last_reviewed = util.now()
  b.put()

  key_name = 'b%d' % blog_id
  memcache.set(key_name, b)


def accept(blog_id):
  '''Mark a blog as accepted'''
  can_write()

  b = get(blog_id)
  if not b:
    return None

  b.accepted = True
  b.put()

  key_name = 'b%d' % blog_id
  memcache.set(key_name, b)


def block(blog_id):
  '''Mark a blog as blocked'''
  can_write()

  b = get(blog_id)
  if not b:
    return None

  b.accepted = False
  b.put()

  key_name = 'b%d' % blog_id
  memcache.set(key_name, b)


def transaction_add_blog(blog_id, blog_name, blog_uri, blocked=False):
  """Transaction function to add a new blog"""
  can_write()

  b = Blog(key_name='b%d' % blog_id)
  b.blog_id = blog_id
  b.name = blog_name
  b.uri = blog_uri
  b.last_updated = util.now()
  if blocked:
    b.accepted = False
  b.put()
  return b


def transaction_update_blog(blog_id, blog_name, blog_uri):
  """Transaction function to update related posts of a post"""
  can_write()

  b = Blog.get_by_key_name('b%d' % blog_id)
  b.last_updated = util.now()
  b.put()
  return b

