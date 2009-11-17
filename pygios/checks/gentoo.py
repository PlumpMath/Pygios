# encoding: utf-8

import sys, logging, re

from decimal import Decimal

from pygios.checks.core                         import CommandCheckRoutine


log = logging.getLogger(__name__)



class CheckGentooServices(CommandCheckRoutine):
    messages = {
            logging.OK: "All services are running normally.",
            logging.WARNING: "One or more service is inactive: %(inactive)s",
            logging.CRITICAL: "One ore more services are not running: %(problem)s",
            logging.ERROR: "Unable to check the status of running services."
        }
    
    @staticmethod
    def to_list(value): return [i.strip() for i in value.split(',')]
    
    kwargs = dict(warning=int, critical=int, include=to_list, exclude=to_list)
    
    include = []
    exclude = []
    
    parser = re.compile(r'^ (\S+)\s+\[\s+(\S+)\s+\]$')
    
    def __init__(self, *args, **kw):
        super(CheckGentooServices, self).__init__(*args, **kw)
        
        self.pipeline = [['rc-status', '-nc'], ['grep', '--perl-regexp', '(broken|stopping|inactive|stopped)']]
        
        if self.include: self.pipeline.append(['grep', '--perl-regexp', '(' + '|'.join(self.include) + ')'])
        if self.exclude: self.pipeline.append(['grep', '--invert-match', '--perl-regexp', '(' + '|'.join(self.exclude) + ')'])
    
    def check(self, exit, stdout, stderr):
        if exit not in [0, 1]: return logging.ERROR, dict()
        
        if not stdout.strip(): return logging.OK, dict()
        
        levels = dict(broken=[], stopping=[], inactive=[], stopped=[], problem=[])
        
        for line in stdout.split("\n"):
            if not line.strip(): continue
            process, status = self.parser.match(line).groups()
            
            levels[status].append(process)
        
        levels['problem'] = levels['broken'] + levels['stopping'] + levels['stopped']
        
        level = logging.OK
        
        if levels['problem']: level = logging.CRITICAL
        elif levels['inactive']: level = logging.WARNING
        
        levels['problem'].extend(levels['inactive'])
        levels['problem'].sort()
        levels['inactive'].sort()
        
        levels['inactive'] = ', '.join(levels['inactive'])
        levels['problem'] = ', '.join(levels['problem'])
        
        return level, levels
