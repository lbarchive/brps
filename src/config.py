import logging

from config_base import *
try:
  from config_custom import *
except ImportError:
  logging.warning('You do not have config_custom.py.')
