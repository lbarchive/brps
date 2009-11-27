# Modified from GAE SDK's django library
import re

from google.appengine.ext import webapp


register = webapp.template.create_template_register()


def intcomma(value):
    """
    Converts an integer to a string containing commas every three digits.
    For example, 3000 becomes '3,000' and 45000 becomes '45,000'.
    """
    orig = str(value)
    new = re.sub("^(-?\d+)(\d{3})", '\g<1>,\g<2>', str(value))
    if orig == new:
        return new
    else:
        return intcomma(new)
register.filter(intcomma)
