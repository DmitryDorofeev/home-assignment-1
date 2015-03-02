import sys
from codecs import getwriter

QUEUE_HOST = 'localhost'
QUEUE_PORT = 33013
QUEUE_SPACE = 0
QUEUE_TAKE_TIMEOUT = 0.1
QUEUE_TUBE = 'api.push_notifications'

HTTP_CONNECTION_TIMEOUT = 30
SLEEP = 0.1
SLEEP_ON_FAIL = 10

WORKER_POOL_SIZE = 10

LOGGING = {
    'version': 1,
    'formatters': {
        'basic': {
            'format': '%(asctime)s %(levelname)s %(threadName)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'stream': getwriter('utf-8')(sys.stderr),
            'formatter': 'basic'
        },
        'null': {
            'class': 'logging.NullHandler',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        'pusher': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
    'root': {
        'propagate': False,
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
