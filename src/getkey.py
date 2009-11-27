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
import md5
import os
import re

from google.appengine.api import memcache
from google.appengine.api.urlfetch import fetch, InvalidURLError
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from brps import blog
import config


RE_BLOG_ID = re.compile(r'http://www\.blogger\.com/rsd\.g\?blogID=(\d+)')


class GetKeyPage(webapp.RequestHandler):
  
  def get(self):
    
    template_values = {
      'config': config,
      }
    path = os.path.join(os.path.dirname(__file__), 'template/getkey.html')
    self.response.out.write(template.render(path, template_values))

  def post(self):
    
    blog_url = self.request.get('blog_url', '')
    template_values = {
      'blog_url': blog_url,
      'config': config,
      }
    if not blog_url:
      template_values['error'] = 'You need to input your blog address!'
    else:
      key = memcache.get('k%s' % blog_url)
      if key:
        template_values['key'] = key
      else:
        try:
          f = fetch(blog_url)
          if f.status_code == 200:
            m = RE_BLOG_ID.search(f.content)
            if m:
              blog_id = m.group(1)
              key = blog.get_blog_key(blog_id)
              memcache.set('k%s' % blog_url, key, 3600)
            else:
              template_values['error'] = 'Can not find blog ID, please ask for <a href="http://groups.google.com/group/blogger-related-posts-service">help</a> with your blog address!'
          else:
            template_values['error'] = 'Can not access to your blog!'
        except InvalidURLError:
          template_values['blog_url'] = ''
          template_values['error'] = '<tt>%s</tt> is not a valid URL!' % blog_url

    path = os.path.join(os.path.dirname(__file__), 'template/getkey.html')
    self.response.out.write(template.render(path, template_values))

  def head(self):
    pass


application = webapp.WSGIApplication(
    [('/getkey', GetKeyPage),
     ],
    debug=True)


def main():
  # Main function
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
