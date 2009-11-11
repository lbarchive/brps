# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2008, 2009  Yu-Jie Lin
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


"""Main file"""


from datetime import timedelta
import simplejson as json
import logging
import os

from google.appengine.api import memcache
from google.appengine.api.datastore_errors import Timeout
from google.appengine.api.urlfetch import DownloadError, fetch
from google.appengine.ext import webapp
from google.appengine.ext.db import stats
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import ApplicationError, CapabilityDisabledError
try:
  # When deployed
  from google.appengine.runtime import DeadlineExceededError
except ImportError:
  # In the development server
  from google.appengine.runtime.apiproxy_errors import DeadlineExceededError

import config
from brps import blog, post, util
from brps.util import json_error, json_str_sanitize, send_json
from brps.post import PrivateBlogError
import Simple24


class HomePage(webapp.RequestHandler):
  """HomePage handler"""
  def get(self):
    """Get method handler"""
    template_values = {
      'before_head_end': config.before_head_end,
      'after_footer': config.after_footer,
      'before_body_end': config.before_body_end,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class StatsPage(webapp.RequestHandler):
  """Statistics Page"""

  def get(self):
    """Get method handler"""
    blogcount = memcache.get('blogcount')
    if blogcount is None:
      total_count, accepted_count, blocked_count = 1, 0, 0
    else:
      total_count, accepted_count, blocked_count = blogcount
    
    db_post_count = memcache.get('db_post_count')
    if db_post_count is None:
      post_stat = stats.KindStat.all().filter('kind_name =', 'Post').get()
      if post_stat is None:
        db_post_count = 'Unavailable'
      else:
        db_post_count = post_stat.count
      memcache.set('db_post_count', db_post_count, 3600 * 3)
     
    template_values = {
      'completed_requests': Simple24.get_count('completed_requests'),
      'chart_uri': Simple24.get_chart_uri('completed_requests'),
      'chart_uri_active_blogs': Simple24.get_chart_uri('active_blogs'),
      'active_blogs_count': Simple24.get_current_hour_count('active_blogs'),
      'total_count': total_count,
      'accepted_count': accepted_count,
      'blocked_count': blocked_count,
      'accepted_percentage': 100.0 * accepted_count / total_count,
      'blocked_percentage': 100.0 * blocked_count / total_count,
      'db_post_count': db_post_count,
      'before_head_end': config.before_head_end,
      'after_footer': config.after_footer,
      'before_body_end': config.before_body_end,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/stats.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class RedirectToStatsPage(webapp.RequestHandler):
  """Redirects to Statistics Page"""

  def get(self):
    """Get method handler"""
    self.redirect("http://brps.appspot.com/stats")


class GetPage(webapp.RequestHandler):
  """Serves relates posts"""

  def get(self):
    """Get method handler"""
    callback = self.request.get('callback')
    try:
      blog_id = int(self.request.get('blog'))
      b = blog.get(blog_id)
      if b is None:
        json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
could not retrieve information for blog from Blogger... \
will retry in a few seconds...', callback)
        return
      if b.accepted == False:
        # Blocked blog
        logging.debug('Blocked blog: %d' % blog_id)
        json_error(self.response, 4, 'This blog is blocked from using \
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a>. \
If you are the blog owner and believe this blocking is \
a mistake, please contact the author of BRPS.', callback)
        return
      post_id = int(self.request.get('post'))
      max_results = int(self.request.get('max_results', post.MAX_POSTS))
      if max_results < 1:
        max_results = 1
      elif max_results > post.MAX_POSTS:
        max_results = post.MAX_POSTS
    except blog.DbBlogReadOnly:
      json_error(self.response, 6, 'BRPS is under maintenance, blog information is readonly right now.', callback)
      return
    except ValueError:
      json_error(self.response, 1, 'Missing Ids', callback)
      return

    try:
      try:
        rlist = post.get_related_list(blog_id, post_id)
        if rlist is None:
          p = post.add(blog_id, post_id)
          rlist = p._relates_['entry']
          key_name = 'b%dp%dl' % (blog_id, post_id)
          memcache.add(key_name, rlist, post.POST_CACHE_TIME)
      except CapabilityDisabledError:
        logging.debug('Caught CapabilityDisabledError')
        json_error(self.response, 2,
            'Unable to process, Google App Engine may be under maintenance.',
            callback)
        return
      except PrivateBlogError:
        json_error(self.response, 5, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
does not support private blog.', callback)
        return
      if rlist is not None:
        relates = {'entry': rlist[:max_results]}
        send_json(self.response, relates, callback)
        Simple24.incr('completed_requests')
        # Add to blog list
        blogs = memcache.get('blogs-1')
        
        curr_hour = util.now().hour
        idx_hour = memcache.get('blogs_hour_index')
        if blogs is None or idx_hour != curr_hour:
          # hour changes
          memcache.set('blogs_hour_index', curr_hour)
          blogs = []
          memcache.set('blogs-1', blogs)
          
        if blog_id not in blogs:
          try:
            if b:
              # Count in
              Simple24.incr('active_blogs')
              # Put blog in
              blogs.append(blog_id)
              memcache.set('blogs-1', blogs)
            else:
              logging.info('Unable to fetch blog info %s, %d.' % \
                  (blog_id, f.status_code))
              json_error(self.response, 5, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
does not support private blog.', callback)
          except Exception, e:
            logging.warning('Unable to add blog %s, %s: %s' % \
                (blog_id, type(e), e))
      else:
        json_error(self.response, 99, 'Unable to get related posts', callback)
    except (DownloadError, DeadlineExceededError, Timeout), e:
      # Should be a timeout, just tell client to retry in a few seconds
      logging.warning('Timeout on b%sp%s, %s: %s' % \
          (blog_id, post_id, type(e), e))
      json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
is processing for this post... will retry in a few seconds...', callback)
    except ApplicationError, e:
      logging.error('ApplicationError on b%sp%s, %s: %s' % \
          (blog_id, post_id, type(e), e))
      json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
is encountering a small problem... will retry in a few seconds...', callback)

application = webapp.WSGIApplication(
    [('/', HomePage),
     ('/stats/?', StatsPage),
     ('/stats.*', RedirectToStatsPage),
     ('/get', GetPage),
     ],
    debug=True)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
