# -*- encoding: utf-8 -*-
import logging.config
import sys


LOGGING_CONFIG_DEFAULTS = dict(
    version=1,
    disable_existing_loggers=False,
    loggers={
        "xn.root": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
            "qualname": "xn.error"
        },
    },
    handlers={
        "console": {
            "class": "logging.FileHandler",
            "formatter": "generic",
            "filename": 'xn.log',
        },
    },
    formatters={
        "generic": {
            "format": "%(asctime)s [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
            "class": "logging.Formatter",
        },
    },
)

logger = logging.getLogger('xn.root')
logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)
