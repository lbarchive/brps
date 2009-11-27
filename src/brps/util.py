# LasTweet lists last tweets to friends
# Copyright (C) 2008  Yu-Jie Lin
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


"""Provides utilities for BRPS"""


import base64
import datetime
import logging

from google.appengine.api import memcache
from google.appengine.api import urlfetch 
from google.appengine.ext import db
from google.appengine.ext import deferred

import simplejson as json


CTRLCHR = [(u'\x01', u''), (u'\x02', u''), (u'\x03', u''),
    (u'\x04', u''), (u'\x05', u''), (u'\x06', u''), (u'\x07', u'\\t'),
    (u'\t', u'\\t'), (u'\x08', u''), (u'\x0b', u''), (u'\x0e', u''), 
    (u'\x0f', u''), (u'\x10', u''), (u'\x11', u''), (u'\x12', u''),
    (u'\x13', u''), (u'\x14', u''),
    (u'\x15', u''), (u'\x16', u''), (u'\x17', u''), (u'\x19', u''),
    (u'\x1a', u''), (u'\x1d', u''),
    (u'\x1e', u''), (u'\x1f', u''), (u'\x8b', '')]


def td_seconds(t):
  """Returns timedelta of now to t in seconds"""
  td = (datetime.datetime.utcnow() - t)
  return td.days * 86400 + td.seconds + td.microseconds / 1000000.0


def now(utc=True):
  """Returns UTC time if utc, otherwise local time"""
  if utc:
    return datetime.datetime.utcnow()
  return datetime.datetime.now()


def fetch(uri, username='', password=''):
  """Can fetch with Basic Authentication"""
  headers = {}
  if username and password:
    headers['Authorization'] = 'Basic ' + base64.b64encode('%s:%s' % \
        (username, password))
  
  f = urlfetch.fetch(uri, headers=headers)
  logging.debug('Fetching %s (%s): %d' % (uri, username, f.status_code))
  return f


def send_json(response, obj, callback):
  """Sends JSON to client-side"""
  json_result = obj
  if not isinstance(obj, (str, unicode)):
    if 'code' not in obj:
      obj['code'] = 0
    json_result = json.dumps(obj)

  response.headers['Content-Type'] = 'application/json'
  if callback:
    response.out.write('%s(%s)' % (callback, json_result))
  else:
    response.out.write(json_result)


def json_error(response, code, msg, callback):
  """Sends error in JSON to client-side
  Error codes:
  # 1 - Missing Ids
  # 2 - GAE problem
  # 3 - Server is processing, try again
  # 4 - Blocked Blog
  # 5 - Private blog is not supported
  # 6 - Datastore is Readonly
  # 99 - Unknown problem
  # TODO sends 500
  """
  send_json(response, {'code': code, 'error': msg}, callback)


def json_str_sanitize(json):
  '''The serialized JSON string from Blogger Data currently contain illegal
  character (to the specification of JSON), they need to be fixed or simplejson
  will complain.'''

  if not isinstance(json, unicode):
    json = json.decode('utf-8')
  for ctrl, rep in CTRLCHR:
    json = json.replace(ctrl, rep)
  return json


def clean_old_posts(POST_AGE_TO_DELETE):
  '''Clean 100 posts and defer itself to clean up to 10000 posts'''

  del_count = memcache.get('post_del_count')
  if del_count is None:
    del_count = 0
  elif del_count >= 10000:
    logging.debug('clean_old_posts: has cleaned up 10000 posts')
    return

  q = db.GqlQuery("SELECT __key__ FROM Post WHERE last_updated < :1",
      now() + datetime.timedelta(days=-1 * POST_AGE_TO_DELETE))
  count = q.count()
  if count:
    # 2009-05-27T08:06:58+0800
    # BadRequestError: cannot delete more than 500 entities in a single call
    if count > 100:
      count = 100
    db.delete(q.fetch(count))
  else:
    logging.debug('clean_old_posts: no more posts to clean up')
    return
  del_count += count
  memcache.set('post_del_count', del_count, 3600 * 1)
  logging.debug('clean_old_posts: %d deletes in total' % del_count)
  if del_count < 10000:
    # Don't run too frequent
    deferred.defer(clean_old_posts, POST_AGE_TO_DELETE, _countdown=60)
    logging.debug('clean_old_posts: redeferred')
  elif count < 100:
    logging.debug('clean_old_posts: no more posts to clean up')
  else:
    logging.debug('clean_old_posts: has cleaned up 10000 posts')
