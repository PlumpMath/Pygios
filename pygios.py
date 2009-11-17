# encoding: utf-8

import                                          logging, logging.config, socket

if not hasattr(logging, 'OK'):
    logging.OK = 15
    logging.addLevelName(logging.OK, 'OK')

from ConfigParser                               import ConfigParser
from datetime                                   import datetime, timedelta

from cos.scheduler                              import Scheduler
from cos.queue                                  import AsyncQueue

from pygios.core                                import Tee, TransitionPipe
from pygios.util                                import get_dotted_object

from pygios                                     import prowlpy



def main():
    socket.setdefaulttimeout(30)

    logging.config.fileConfig('sample.ini')


    log = logging.getLogger('pygios')


    config = ConfigParser()
    config.read('sample.ini')

    monitor = [i.strip() for i in config.get('monitor', 'keys').split(',') if i.strip()]

    log.info("Loaded configuration: %d monitor%s.", len(monitor), '' if len(monitor) == 1 else 's')


    log.debug("Preparing scheduler.")

    scheduler = Scheduler()


    log.debug("Preparing logger task.")


    tp = AsyncQueue()
    lq = AsyncQueue()

    scheduler.add(Tee(input=tp))
    scheduler.add(TransitionPipe(input=lq, output=tp))


    for name in monitor:
        log.debug("Configuring %s.", name)

        kw = dict(config.items('monitor_' + name))

        plugin = get_dotted_object(kw.pop('plugin'))

        if 'schedule' in kw:
            schedule = kw.pop('schedule')
            kw['every'] = timedelta(**dict([(i, int(j)) for i, j in config.items('schedule_' + schedule)]))

        for key in kw.iterkeys():
            if key in plugin.kwargs:
                kw[key] = plugin.kwargs[key](kw[key])

        log.info("%s(%r)", name, kw)

        scheduler.add(plugin(name, lq, **kw))




    scheduler.run()



if __name__ == '__main__':
    main()