# encoding: utf-8

"""Coroutines for the processing of pipes."""


import logging

from cos.queue import Queue, AsyncQueue


log = logging.getLogger(__name__)



class Pipe(object):
    def __init__(self, input=None, output=None):
        self.input = input if input else AsyncQueue()
        self.output = output if output else AsyncQueue()
    
    def process(self, data):
        return data
    
    def __call__(self):
        while True:
            if callable(self.input):
                data = yield self.input()
            elif isinstance(self.input, Queue):
                data = yield self.input.get()
            else:
                raise TypeError('data is not callable or quque: %r' % (repr(self.input), ))
            
            result = self.process(data)
            
            if not result: continue
            
            if callable(self.output):
                yield self.output(result)
            elif isinstance(self.output, Queue):
                yield self.output.put(result)


class Tee(Pipe):
    """Echos input to the standard Python logging system.
    
    Handles input in one of several formats:
    
        Plain string, in which case the name is 'tee' and level is 'info':
        
            'message'
    
        Dictionary with name and level optional, missing values interpreted as above:
        
            dict(name='', level='', message='')
    
        2-tuple or 3-tuple, missing values interpreted as above:
    
            (level, message)
            (name, level, message)
            (name, level, message, ...)
        
        The string representation of the message will be logged, allowing non-string values to be passed through the pipe.
    """
    
    @staticmethod
    def _name(data):
        if not isinstance(data, (tuple, dict)):
            return 'tee'
        
        if isinstance(data, tuple):
            if len(data) == 4: return data[0]
            return 'tee'
        
        if isinstance(data, dict):
            if 'name' in data: return data['name']
            return 'tee'
    
    @staticmethod
    def _level(data):
        if not isinstance(data, (tuple, dict)):
            return logging.INFO
        
        if isinstance(data, tuple):
            if len(data) >= 2: return data[1]
            return logging.INFO
        
        if isinstance(data, dict):
            if 'name' in data: return data['name']
            return logging.INFO
    
    @staticmethod
    def _message(data):
        if not isinstance(data, (tuple, dict)):
            return str(data)
        
        if isinstance(data, tuple):
            return str(data[min(2,len(data)-1)])
        
        if isinstance(data, dict):
            return data['message']
    
    def __init__(self, input=None, output=None, name=None, level=None, message=None, forward=True):
        super(Tee, self).__init__(input, output)
        self.name = self._name if not name else name
        self.level = self._level if not level else level
        self.message = self._message if not message else message
        self.forward = forward
    
    def process(self, data):
        name, level, message, kw = data
        logger = logging.getLogger('check.' + name)
        logger.log(level, message % kw)
        return data if self.forward else (message % kw) 


class TransitionPipe(Pipe):
    """A 3-way pipe that forwards unique state changes."""
    
    def __init__(self, input=None, output=None):
        from collections import defaultdict
        self.states = defaultdict(lambda: Queue((logging.NOTSET, ), 5))
        
        super(TransitionPipe, self).__init__(input, output)
    
    def process(self, data):
        name, level, message, kw = data
        
        log.debug("%r, %r, %r, %r", name, level, message, kw)
        
        history = self.states[name]
        history.put(level)
        self.states[name] = history
        
        log.debug('history.queue: %r', history.queue)
        log.debug('history.queue[-2]: %r', history.queue[-2])
        
        if history.queue[-2] == level:
            return
        
        return (name, level, message, kw)
