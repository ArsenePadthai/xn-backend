# -*- encoding: utf-8 -*-
import logging
import os

import coloredlogs
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_log_request_id import RequestIDLogFilter
from flask_restful import Api


bcrypt = Bcrypt()
cache = Cache(config={'CACHE_TYPE': 'simple'})


def init_logger(app):
    if not app.debug:
        if app.config.get('LOG_DIR'):
            from logging.handlers import TimedRotatingFileHandler

            # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
            handler = TimedRotatingFileHandler(
                os.path.join(app.config['LOG_DIR'], 'TelecomMonitorWebTool.app.log'),
                'midnight'
            )
        else:
            handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter('[%(asctime)s] %(process)d %(request_id)s %(levelname)s - %(message)s'))
        handler.addFilter(RequestIDLogFilter())
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        logging.getLogger('werkzeug').addHandler(handler)
        logging.getLogger().addHandler(handler)
        # app.logger.debug('test debug output')
        # app.logger.info('test info output')
        # app.logger.warning('test warning output')
        # app.logger.error('test error output')
    else:
        fmt = '%(asctime)s %(hostname)s %(name)s[%(process)d] %(request_id)s %(levelname)s %(message)s'

        coloredlogs.install(
            logger=app.logger,
            level='DEBUG',
            fmt=fmt,
        )
        coloredlogs.install(
            logger=logging.getLogger('werkzeug'),
            level='DEBUG',
            fmt=fmt,
        )
        logging.getLogger('werkzeug').propagate = False
        coloredlogs.install(
            level='DEBUG',
            fmt=fmt,
        )

        for h in app.logger.handlers + logging.getLogger('werkzeug').handlers + logging.getLogger().handlers:
            h.addFilter(RequestIDLogFilter())


def init_cache(app):
    global cache
    cache.init_app(app)


def init_api(app):
    return Api(app)
