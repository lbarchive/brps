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


from datetime import timedelta

from google.appengine.api import memcache
from google.appengine.api.labs.taskqueue import TaskAlreadyExistsError
from google.appengine.ext import db, webapp
from google.appengine.ext import deferred
from google.appengine.ext.webapp.util import run_wsgi_app

from brps import blog, util


# In days
POST_AGE_TO_DELETE = 2


class CleanUp(webapp.RequestHandler):
  
  def get(self):

    try:
      deferred.defer(util.clean_old_posts, POST_AGE_TO_DELETE)
      self.response.out.write('cleanoldposts: Deferred.')
    except TaskAlreadyExistsError:
      self.response.out.write('cleanoldposts: Already deferred.')
      pass


class BlogCount(webapp.RequestHandler):
  
  def get(self):

    def get_count(q):
      r = q.fetch(1000)
      count = 0
      while True:
        count += len(r)
        if len(r) < 1000:
          break
        q.filter('__key__ >', r[-1])
        r = q.fetch(1000)
      return count

    q = db.Query(blog.Blog, keys_only=True)
    q.order('__key__')
    total_count = get_count(q)

    q = db.Query(blog.Blog, keys_only=True)
    q.filter('accepted =', True)
    q.order('__key__')
    accepted_count = get_count(q)
    
    q = db.Query(blog.Blog, keys_only=True)
    q.filter('accepted =', False)
    q.order('__key__')
    blocked_count = get_count(q)

    memcache.set('blogcount', (total_count, accepted_count, blocked_count))
    self.response.out.write('Total: %d\nAccepted: %d\nBlocked: %d' % (total_count, accepted_count, blocked_count))


application = webapp.WSGIApplication([
    ('/admin/blogcount', BlogCount),
    ('/admin/defer_cleanup', CleanUp),
    ],
    debug=True)


def main():
  
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
