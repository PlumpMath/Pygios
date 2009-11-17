# encoding: utf-8

import sys, logging

from decimal import Decimal

from pygios.checks.core                         import NumericCommandCheckRoutine


log = logging.getLogger(__name__)



class CheckUserCount(NumericCommandCheckRoutine):
    messages = {
            logging.OK: "The number of active users, %(count)d, is within acceptable range.",
            logging.WARNING: "The number of active users, %(count)d, is high.",
            logging.CRITICAL: "The number of active users, %(count)d, is critically high.",
            logging.ERROR: "Unable to check the number of active users."
        }
    
    @staticmethod
    def to_list(value): return [i.strip() for i in value.split(',')]
    
    kwargs = dict(warning=int, critical=int, include=to_list, exclude=to_list)
    
    include = []
    exclude = []
    
    def __init__(self, *args, **kw):
        super(CheckUserCount, self).__init__(*args, **kw)
        self.pipeline = [['who']]
        if self.include: self.pipeline.append(['grep', '--perl-regexp', '(' + '|'.join(self.include) + ')'])
        if self.exclude: self.pipeline.append(['grep', '--invert-match', '--perl-regexp', '(' + '|'.join(self.exclude) + ')'])
        self.pipeline.append(['wc', '-l'])
    
    def check(self, exit, stdout, stderr):
        if exit != 0: return logging.ERROR, dict()
        kw = dict(count=int(stdout.strip()))
        return super(CheckUserCount, self).check(kw['count']), kw
