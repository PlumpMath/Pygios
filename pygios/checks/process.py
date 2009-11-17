# encoding: utf-8

import sys, logging

from decimal import Decimal

from pygios.checks.core                         import NumericCommandCheckRoutine


log = logging.getLogger(__name__)



class CheckProcessCount(NumericCommandCheckRoutine):
    messages = {
            logging.OK: "The number of processes, %(count)d, is within the acceptable range.",
            logging.WARNING: "The number of processes, %(count)d, is high.",
            logging.CRITICAL: "The number of processes, %(count)d, is critically high.",
            logging.ERROR: "Unable to check process count."
        }
    
    kwargs = dict(warning=int, critical=int, user=str)
    
    warning = 50
    critical = 100
    user = None
    
    def __init__(self, *args, **kw):
        super(CheckProcessCount, self).__init__(*args, **kw)
        self.pipeline = [['ps', 'ax']] + ( [['grep', self.user]] if self.user is not None else [] ) + [['wc', '-l']]
    
    def check(self, exit, stdout, stderr):
        if exit != 0: return logging.ERROR, dict()
        kw = dict(count=int(stdout.strip()))
        return super(CheckProcessCount, self).check(kw['count']), kw


class CheckProcessMemory(NumericCommandCheckRoutine):
    messages = {
            logging.OK: "Process memory usage is within acceptable range.",
            logging.WARNING: "Memory usage is high (%(percent)s%%, %(kbytes)d Kbytes) for process %(command)s owned by %(user)s.",
            logging.CRITICAL: "Memory usage is critical (%(percent)s%%, %(kbytes)d Kbytes) for process %(command)s owned by %(user)s.",
            logging.ERROR: "Unable to check process memory usage."
        }
    
    @staticmethod
    def to_list(value): return [i.strip() for i in value.split(',')]
    
    kwargs = dict(warning=int, critical=int, include=to_list, exclude=to_list)
    
    include = []
    exclude = []
    
    def __init__(self, *args, **kw):
        super(CheckProcessMemory, self).__init__(*args, **kw)
        
        if sys.platform == 'darwin':
            self.pipeline = [['ps', 'axm', '-o', 'rss', '-o', '%mem', '-o', 'login', '-o', 'command']]
        
        elif sys.platform == 'linux':
            self.pipeline = [['ps', 'ax', '-o', 'rss', '-o', '%mem', '-o', 'euser', '-o', 'command', '--sort=-rss']]
        
        if self.include: self.pipeline.append(['grep', '--perl-regexp', '(' + '|'.join(self.include) + ')'])
        if self.exclude: self.pipeline.append(['grep', '--invert-match', '--perl-regexp', '(' + '|'.join(self.exclude) + ')'])
        
        self.pipeline.extend([['head', '-n', '2'], ['tail', '-n', '1']])
    
    def check(self, exit, stdout, stderr):
        if exit != 0: return logging.ERROR, dict()
        
        import re
        _ = re.compile(r'\s+').split(stdout.strip())
        
        kw = dict()
        for i, j, k in [(0, 'kbytes', int), (1, 'percent', Decimal), (2, 'user', str), (3, 'command', lambda s: s.split('/')[-1])]:
            kw[j] = k(_[i])
        
        return super(CheckProcessMemory, self).check(kw['kbytes']), kw
