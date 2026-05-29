import logging
from logging.config import dictConfig
import sys

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(levelname)s | %(asctime)s | %(name)s | %(message)s"},
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stderr,
            "level": "ERROR",
        },
    },
    "loggers": {
        "app": {
            "handlers": ["stdout", "stderr"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

dictConfig(LOGGING_CONFIG)

logger = logging.getLogger("app")
