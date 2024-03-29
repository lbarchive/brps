# Blogger.com Related Posts Service (http://brps.appspot.com/)
#
# Copyright (C) 2008, 2009, 2010  Yu-Jie Lin
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
import md5
import os

from google.appengine.api import memcache
from google.appengine.api.datastore_errors import Timeout
from google.appengine.api.labs.taskqueue import TaskAlreadyExistsError
from google.appengine.api.urlfetch import DownloadError, fetch
from google.appengine.ext import webapp
from google.appengine.ext import deferred
from google.appengine.ext.db import stats
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime.apiproxy_errors import ApplicationError, CapabilityDisabledError
from google.appengine.runtime import DeadlineExceededError

import config
from brps import blog, post, util
from brps.util import json_error, send_json
from brps.post import PrivateBlogError
import Simple24


class HomePage(webapp.RequestHandler):
  
  def get(self):
    
    template_values = {
      'config': config,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/home.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class GetKeyPage(webapp.RequestHandler):
  
  def get(self):

    self.redirect('/install')

  def head(self):
    pass

class InstallPage(webapp.RequestHandler):
  
  def get(self):
    
    template_values = {
      'config': config,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/install.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class DonatePage(webapp.RequestHandler):
  
  def get(self):
    
    template_values = {
      'config': config,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/donate.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class StatsPage(webapp.RequestHandler):

  def get(self):
    
    blogcount = memcache.get('blogcount')
    if blogcount is None:
      total_count, accepted_count, blocked_count = None, None, None
    else:
      total_count, accepted_count, blocked_count = blogcount

    if total_count is None:
      try:
        deferred.defer(util.blog_count)
        logging.debug('blog_count: Deferred.')
      except TaskAlreadyExistsError:
        logging.debug('blog_count: Already deferred.')
        pass
      review_count = None
    else:
      review_count = total_count - accepted_count - blocked_count

    db_post_count = memcache.get('db_post_count')
    if db_post_count is None:
      post_stat = stats.KindStat.all().filter('kind_name =', 'Post').get()
      if post_stat is None:
        db_post_count = 'Unavailable'
      else:
        db_post_count = post_stat.count
      memcache.set('db_post_count', db_post_count, 3600 * 3)
     
    template_values = {
      'config': config,
      'completed_requests': Simple24.get_count('completed_requests'),
      'chart_uri': Simple24.get_chart_uri('completed_requests'),
      'chart_uri_active_blogs': Simple24.get_chart_uri('active_blogs'),
      'active_blogs_count': Simple24.get_current_hour_count('active_blogs'),
      'db_post_count': db_post_count,
      }
    if total_count:
      template_values['total_count'] = total_count
      template_values['accepted_count'] = accepted_count
      template_values['blocked_count'] = blocked_count
      template_values['review_count'] = review_count
      template_values['accepted_percentage'] = 100.0 * accepted_count / total_count
      template_values['blocked_percentage'] = 100.0 * blocked_count / total_count
      template_values['review_percentage'] = 100.0 * review_count / total_count
    path = os.path.join(os.path.dirname(__file__), 'template/stats.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


class GetPage(webapp.RequestHandler):
  # Serves relates posts
  def get(self):
    
    callback = self.request.get('callback')
    try:
      blog_id = int(self.request.get('blog'))
      key = self.request.get('key', '')
      b = blog.get(blog_id, key)
      if b is None:
        json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
could not retrieve information for blog from Blogger... \
will retry in a few seconds...', callback)
        return
      if b.accepted == False:
        # Blocked blog
        json_error(self.response, 4, 'This blog is blocked from using \
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a>. \
If you are the blog owner and believe this blocking is \
a mistake, please contact the author of BRPS.', callback)
        return
      if not b.accepted:
        # Need to check the key
        if key:
          if key != blog.get_blog_key(blog_id):
            raise blog.InvalidBlogKeyError('The key is not valid.')
        else:
          raise blog.InvalidBlogKeyError('The key is not supplied.')
      post_id = int(self.request.get('post'))
      max_results = int(self.request.get('max_results', post.MAX_POSTS))
      if max_results < 1:
        max_results = 1
      elif max_results > post.MAX_POSTS:
        max_results = post.MAX_POSTS
    except blog.DbBlogReadOnly:
      json_error(self.response, 6, 'BRPS is under maintenance, blog information\
 is readonly right now.', callback)
      return
    except blog.InvalidBlogKeyError, e:
      json_error(self.response, 99, e.message + ' Please go to <a \
href="http://brps.appspot.com/">BRPS</a> to obtain one. If you are reading \
this, please relay the message to the owner of this blog.', callback)
      return
    except ValueError:
      json_error(self.response, 1, 'Missing Ids', callback)
      return
    except (DownloadError, DeadlineExceededError, Timeout), e:
      json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
is processing for this post... will retry in a few seconds...', callback)
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
        logging.warning('Caught CapabilityDisabledError')
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
              logging.warning('Unable to fetch blog info %s, %d.' % \
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
      json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
is processing for this post... will retry in a few seconds...', callback)
    except ApplicationError, e:
      json_error(self.response, 3, '\
<a href="http://brps.appspot.com/">Blogger Related Posts Service</a> \
is encountering a small problem... will retry in a few seconds...', callback)

  def head(self):
    pass


application = webapp.WSGIApplication([
    ('/', HomePage),
    ('/getkey', GetKeyPage),
    ('/install', InstallPage),
    ('/donate', DonatePage),
    ('/stats/?', StatsPage),
    ('/get', GetPage),
    ], debug=config.DEBUG)


def main():
  # Main function
  webapp.template.register_template_library('humanize')
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
