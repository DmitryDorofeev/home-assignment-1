import sys
from codecs import getwriter

INPUT_QUEUE_HOST = 'localhost'
INPUT_QUEUE_PORT = 33013
INPUT_QUEUE_SPACE = 0
INPUT_QUEUE_TUBE = 'url.queue'

OUTPUT_QUEUE_HOST = 'localhost'
OUTPUT_QUEUE_PORT = 33013
OUTPUT_QUEUE_SPACE = 0

OUTPUT_QUEUE_TUBE = 'url_redirect.queue'

WORKER_POOL_SIZE = 10
QUEUE_TAKE_TIMEOUT = 0.1

SLEEP = 10

HTTP_TIMEOUT = 3
MAX_REDIRECTS = 30
RECHECK_DELAY = 300
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"

CHECK_URL = "http://t.mail.ru"

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
