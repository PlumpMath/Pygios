# encoding: utf-8

import logging

from time import sleep
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
from pygios.checks.core import CheckRoutine


class CheckPHP(CheckRoutine):
    kwargs = {
            'timeout': int
        }
    
    timeout = 5
    
    messages = {
            logging.OK: "PHP is running correctly.",
            logging.WARNING: "PHP returned with non-zero status code %(value)d.",
            logging.CRITICAL: "PHP is not able to process requests.",
            logging.ERROR: "Error attempting to call PHP."
        }
    
    def check(self):
        start = datetime.now()
        
        php = Popen(['/usr/bin/php', '-r', 'phpinfo(1);'], stdout=PIPE)
        value = php.poll()
        
        while True:
            sleep(1.0)
            
            value = php.poll()
            
            if value is None and start - datetime.now() < timedelta(seconds=self.timeout):
                continue
            
            if isinstance(value, int): break
            
            php.terminate()
            
            return logging.CRITICAL, dict()
        
        return logging.OK if value == 0 else logging.WARNING, dict(value=value)
