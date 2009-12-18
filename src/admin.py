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
from datetime import datetime, timedelta
import logging
import os
import re
import urllib

from google.appengine.api import memcache
from google.appengine.api.urlfetch import fetch, InvalidURLError
from google.appengine.ext import db, webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

import config
from brps import blog, post, util
from brps.util import json_error, send_json
import Simple24


RE_BLOG_ID = re.compile(r'http://www\.blogger\.com/rsd\.g\?blogID=(\d+)')


class AdminPage(webapp.RequestHandler):

  def get(self):
    
    template_values = {
      'config': config,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/admin.html')
    self.response.out.write(template.render(path, template_values))


class ReviewPage(webapp.RequestHandler):

  def get(self):

    query = db.Query(blog.Blog)
    query.filter('last_reviewed =', None)
    query.filter('accepted =', None)
    query.order('last_reviewed')
    blogs = query.fetch(10)

    query = db.Query(blog.Blog)
    query.filter('last_reviewed <', util.now() + timedelta(seconds=-1 * config.BLOG_REVIEW_INTERVAL))
    query.filter('accepted =', None)
    query.order('last_reviewed')
    template_values = {
      'new_blogs': blogs,
      'old_blogs': [b for b in query.fetch(10) if b.last_reviewed != None],
      }
    path = os.path.join(os.path.dirname(__file__), 'template/admin_review.html')
    self.response.out.write(template.render(path, template_values))


class ReviewedJSON(webapp.RequestHandler):

  def get(self):

    callback = self.request.get('callback')
    blog_id = int(self.request.get('blog_id'))
    if not blog_id:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    b = blog.get(blog_id)
    if not b:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    blog.reviewed(blog_id)
    send_json(self.response, {'blog_id': str(blog_id)}, callback)


class BlockJSON(webapp.RequestHandler):

  def get(self):

    callback = self.request.get('callback')
    blog_id = int(self.request.get('blog_id'))
    if not blog_id:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    b = blog.get(blog_id)
    if not b:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    blog.block(blog_id)
    send_json(self.response, {'blog_id': str(blog_id)}, callback)


class AcceptJSON(webapp.RequestHandler):

  def get(self):

    callback = self.request.get('callback')
    blog_id = int(self.request.get('blog_id'))
    if not blog_id:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    b = blog.get(blog_id)
    if not b:
      json_error(self.response, 99, callback, 'No blog_id specified')
      return

    blog.accept(blog_id)
    send_json(self.response, {'blog_id': str(blog_id)}, callback)


class UnblockPage(webapp.RequestHandler):

  def get(self):
    
    blog_url = urllib.unquote(self.request.get('blog_url', ''))
    template_values = {
      'blog_url': blog_url,
      'config': config,
      }

    if blog_url:
      try:
        f = fetch(blog_url)
        if f.status_code == 200:
          m = RE_BLOG_ID.search(f.content)
          if m:
            blog_id = m.group(1)
            if blog.unblock(int(blog_id)):
              template_values['error'] = 'Unblocked.'
            else:
              template_values['error'] = 'Cannot find a record of the blog!'
          else:
            template_values['error'] = 'Can not find blog ID!'
        else:
          template_values['error'] = 'Can not access to the blog!'
      except InvalidURLError:
        template_values['blog_url'] = ''
        template_values['error'] = '<tt>%s</tt> is not a valid URL!' % blog_url

    path = os.path.join(os.path.dirname(__file__), 'template/admin_unblock.html')
    self.response.out.write(template.render(path, template_values))
    

application = webapp.WSGIApplication(
    [('/admin/?', AdminPage),
     ('/admin/review', ReviewPage),
     ('/admin/reviewed.json', ReviewedJSON),
     ('/admin/accept.json', AcceptJSON),
     ('/admin/block.json', BlockJSON),
     ('/admin/unblock', UnblockPage),
     ],
    debug=True)


def main():
  """Main function"""
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
