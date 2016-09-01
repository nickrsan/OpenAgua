#!/usr/bin/python3
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/OpenAguaDSS/")

from OpenAgua import app as application
application.secret_key = '\x1dW5\xc5\x85\xadr~\xc6_ww\xdd\x00\xf0m\xb0rR%7\xd3\x9b\xed'
