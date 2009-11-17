# encoding: utf-8

import logging
import urllib

from httplib import responses

from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from pygios.checks.core import CheckRoutine


log = logging.getLogger("test")


class CheckHTTPRequest(CheckRoutine):
    kwargs = {
            'timeout': int,
            'url': str
        }
    
    timeout = 5
    url = None
    
    levels = {
        logging.OK: [200, 201, 202, 203, 204, 205, 206],
        logging.WARNING: [300, 301, 302, 303, 304, 305, 306, 307],
        logging.CRITICAL: [
                400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417,
                500, 501, 502, 503, 504, 505
            ]
    }
    
    messages = {
            logging.OK: "Website returned HTTP %(status)i %(response)s.\n%(url)s",
            logging.WARNING: "Website requested redirection, HTTP %(status)i %(response)s.\n%(url)s",
            logging.CRITICAL: "Server reported error, HTTP %(status)i %(response)s.\n%(url)s",
            logging.ERROR: "Unable to determine URL status.\n%(url)s"
        }
    
    def check(self):
        try:
            request = urllib.urlopen(self.url)
            
            data = request.read()
            headers = request.info().headers
            status = request.getcode()
        
        except IOError:
            return logging.ERROR, dict(url=self.url)
        
        except:
            log.exception("Error checking URL(%s).", self.url)
            return logging.ERROR, dict(url=self.url)
        
        for i, j in self.levels.iteritems():
            if status in j:
                return i, dict(status=status, response=responses[status], url=self.url)
