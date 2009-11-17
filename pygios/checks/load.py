# encoding: utf-8

import os, logging

from decimal import Decimal

from pygios.checks.core                         import NumericCheckRoutine

log = logging.getLogger(__name__)


class CheckLoadAverage(NumericCheckRoutine):
    messages = {
            logging.OK: "Load average of %(average)0.2f is within acceptable range.",
            logging.WARNING: "Load average of %(average)0.2f is high.",
            logging.CRITICAL: "Load average of %(average)0.2f is critically high.",
            logging.ERROR: "Unable to determine load average."
        }
    
    kw = dict(warning=Decimal, critical=Decimal, average=int)
    
    warning = Decimal('3')
    critical = Decimal('6')
    average = 1
    
    def __init__(self, *args, **kw):
        super(CheckLoadAverage, self).__init__(*args, **kw)
        self.average = {1:0, 5:1, 15:2}.get(self.average, 0)
    
    def check(self):
        averages = tuple([Decimal(str(i)) for i in os.getloadavg()])
        
        kw = dict(average=averages[self.average], one=averages[0], five=averages[1], fifteen=averages[2])
        return kw['average'], kw