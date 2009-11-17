# encoding: utf-8

import logging, platform

class TurboMailHandler(logging.Handler):
    """A class which sends records out via e-mail.

    The built-in SMTPHandler is insufficient for most jobs, restricting
    developers to unauthenticated communication over the standard port,
    with little control over additional delivery options.

    This handler should be configured using the same configuration
    directives that TurboMail itself understands.  If you do not specify
    `mail.on` in the configuration, this handler will attempt to use
    a previously configured TurboMail environment.

    Be sure that TurboMail is running before messages are emitted using
    this handler, and be careful how many notifications get sent.

    It is suggested to use background delivery using the 'demand' manager.

    Configuration options for this handler are as follows::

        * mail.handler.priorities = [True/False]
          Set message priority using the following formula:
            record.levelno / 10 - 3
    
        * 
    """

    def __init__(self, *args, **config):
        """Initialize the instance, optionally configuring TurboMail itself.
        
        If no additional arguments are supplied to the handler, re-use any
        existing running TurboMail configuration.
        
        To get around limitations of the INI parser, you can pass in a tuple
        of name, value pairs to populate the dictionary.
        """
        
        logging.Handler.__init__(self)
        
        import turbomail
        
        self.config = dict()
        
        if args:
            config.update(dict(zip(*[iter(args)]*2)))
        
        if config and 'mail.on' in config:
            # Initilize TurboMail using the configuration directives passed
            # to this handler, generally from an INI configuration file.
            turbomail.interface.start(config)
        
        
        
        # If we get a configuration that doesn't explicitly start TurboMail
        # we use the configuration to populate the Message instance.
        self.config = config
    
    def render_subject(self, record):
        data = dict(record.__dict__)
        data['message'] = record.getMessage()
        data['hostname'] = platform.uname()[1]
        
        return self.config.get(
                'mail.message.subject',
                "[%(name)s %(levelname)s on %(hostname)s] Python logging notification."
            ) % data
    
    def emit(self, record):
        """Emit a record."""
        import turbomail
        
        try:
            message = turbomail.Message()
            
            if self.config:
                for i, j in self.config.iteritems():
                    if i.startswith('mail.message'):
                        setattr(message, i.split('.')[-1], j)
            
            message.subject = self.render_subject(record)
            message.headers = dict()
            
            for i, j in [
                    ('filename', 'File-Name'),
                    ('funcName', 'Function'),
                    ('levelname', 'Level'),
                    ('levelno', 'Level-ID'),
                    ('module', 'Module'),
                    ('process', 'PID'),
                    ('thread', 'Thread-ID'),
                    ('threadName', 'Thread-Name')
                ]:
                message.headers['X-Loggger-' + j] = getattr(record, i)
            
            message.plain = self.format(record)
            message.send()
        
        except (KeyboardInterrupt, SystemExit):
            raise
        
        except:
            self.handleError(record)
