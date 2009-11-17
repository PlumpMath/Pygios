# encoding: utf-8

import os, logging

from datetime import datetime, timedelta
from decimal import Decimal
from subprocess import Popen, PIPE

from cos.queue                                  import Queue
from cos.routines.system                        import SleepTask, WaitBase


log = logging.getLogger(__name__)



class WaitForActivate(WaitBase):
    kind = 'activation'


class Callable(object):
    def __init__(self):
        self.active = True
        self.called = Queue(maxlen=25)
    
    def __call__(self):
        self.called.put(datetime.now())



class CheckRoutine(Callable):
    """Check routines are scheduled coroutines that pass logging information to asynchronous queues.
    
    @type kwargs: dict
    @cvar kwargs: A mapping of configuration variables to typecasting callbacks.
                  Often used with simple types, e.g. int, str, etc., but can be used with more complicated callbacks.
                  These are automatically saved to attributes of the class instance.
    
    @type messages: dict
    @cvar messages: A mapping of logging levels (OK, WARNING, and CRITICAL required, but others can be defined) to template strings.
                    Template strings are passed in the dictionary returned by the check method.
    
    @type name: str
    @ivar name: The name given in the configuration for this specific check routine setup.
    
    @type target: callable, AsyncQueue
    @ivar target: The target queue that messages should be placed within, or a callback.
    
    @type every: timedelta
    @ivar every: The frequency at which this check should be performed.
                 If this check should be scheduled for a first run in the future, wrap it.
    
    @type host: UUID
    @ivar host: A host reference.  This is used for proxying file and application requests over a SSH tunnel.
    
    @type history: Queue
    @ivar history: A circular queue of the last n B{state changes}.
    """
    
    kwargs = {}
    messages = {
            logging.OK: "OK",
            logging.WARNING: "WARNING",
            logging.CRITICAL: "CRITICAL",
            logging.ERROR: "ERROR"
        }
    
    def __init__(self, name, target, host=None, every=None, **kw):
        super(CheckRoutine, self).__init__()
        
        self.name = name
        self.target = target
        self.host = host
        self.every = every
        self.history = Queue(maxlen=25)
        
        for attr, callback in self.kwargs.iteritems():
            if attr not in kw: continue
            value = kw.get(attr, None)
            setattr(self, attr, callback(value))
    
    def __call__(self):
        if not self.active: yield WaitForActivation(None)
        
        super(CheckRoutine, self).__call__()
        
        while True:
            level, kw = self.process()
            
            if self.target:
                if callable(self.target): yield self.target((self.name, level, self.messages[level], kw))
                elif isinstance(self.target, Queue): yield self.target.put((self.name, level, self.messages[level], kw))
            
            yield SleepTask(until=self.every)
    
    def process(self):
        """The process function must always return a level and keyword dictionary."""
        return self.check()
    
    def check(self):
        """The generic check method returns a level and keyword dictionary."""
        raise NotImplementedError()
        # return (level, **kw)


class NumericCheckRoutine(CheckRoutine):
    """Process comparable values using thresholds.
    
    The value returned by the check method must be comparable using the greater than operator to the values stored in the warning and critical attributes.
    
    It's up to the individual check routine to typecast warning and critical kwargs.
    """
    
    def __init__(self, name, target, host=None, **kw):
        super(NumericCheckRoutine, self).__init__(name, target, host, **kw)
        
        self.thresholds = [(self.warning, logging.WARNING), (self.critical, logging.CRITICAL)]
    
    def process(self):
        """Automatically calculate the logging level based on threshold values."""
        value, kw = self.check()
        
        level = logging.OK
        for i, j in self.thresholds:
            if value > i: level = j
        
        return level, kw
    
    def check(self):
        """The numeric check method returns a comparable numeric value and keyword dictionary."""
        raise NotImplementedError()
        #return (value, **kw)


class CommandCheckRoutine(CheckRoutine):
    pipeline = []
    
    def process(self):
        pipes = []
        
        pipeline = self.pipeline() if callable(self.pipeline) else self.pipeline
        for cmd in pipeline:
            pipes.append(Popen(cmd() if callable(cmd) else cmd, stdout=PIPE, stdin=pipes[-1].stdout if pipes else None))
        
        stdout, stderr = pipes[-1].communicate()
        level, kw = self.check(pipes[-1].returncode, stdout, stderr)
        
        return level, kw
    
    def check(self, exit, stdout, stderr):
        raise NotImplementedError()
        #return (level, kw)


class NumericCommandCheckRoutine(CommandCheckRoutine):
    def __init__(self, name, target, host=None, **kw):
        super(NumericCommandCheckRoutine, self).__init__(name, target, host, **kw)
        
        self.thresholds = [(self.warning, logging.WARNING), (self.critical, logging.CRITICAL)]
    
    def check(self, value):
        """Call super() and pass this the numeric value."""
        level = logging.OK
        for i, j in self.thresholds:
            if value > i: level = j
        
        return level
