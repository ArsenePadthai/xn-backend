from datetime import timedelta

from flask_env import MetaFlaskEnv


class DefaultConfiguration(metaclass=MetaFlaskEnv):
    ENV_LOAD_ALL = True
    ENV_PREFIX = 'XN_'

    DEBUG = False  # make sure DEBUG is off unless enabled explicitly otherwise
    LOG_DIR = '.'  # create log files in current working directory

    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml',
        'application/json',
        'application/javascript',
        'image/jpeg',
        'image/png',
        'image/bmp',
        'image/gif',
        'application/x-font-woff',
        'application/x-font-ttf',
        'application/x-font-otf',
        'application/octet-stream',
    ]

    REDIS_CONFIGURATION = {
        'host': 'localhost',
    }

    CELERY_ACCEPT_CONTENT = ['pickle', 'json', 'msgpack', 'yaml']
    CELERYD_WORKER_CONCURRENCY = 1

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_AUTH_URL_RULE = None
    JWT_EXPIRATION_DELTA = timedelta(seconds=60*60*24)

    LIST_FETCH_LIMIT_LEN = 15

    MEMCACHED_SERVER = None

