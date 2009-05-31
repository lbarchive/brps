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

from google.appengine.ext import db, webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from brps import post, util


class CleanUp(webapp.RequestHandler):
  
  def get(self):
    
    posts = post.Post.all()
    posts.filter('last_updated <', util.now() + timedelta(days=-30))
    posts.order('last_updated')
    count = posts.count()
    if count:
      # 2009-05-27T08:06:58+0800
      # BadRequestError: cannot delete more than 500 entities in a single call
      if count > 100:
        count = 100
      self.response.out.write('Trying to delete %d posts...' % count)
      db.delete(posts.fetch(count))
      self.response.out.write('deleted succesfully.')
    else:
      self.response.out.write('No posts need to be removed')


application = webapp.WSGIApplication(
    [('/admin/cleanoldposts', CleanUp),
     ],
    debug=True)


def main():
  
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
