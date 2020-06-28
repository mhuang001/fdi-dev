logdict = {
    "version": 1,
    "formatters": {
        "short": {
            "format": "%(funcName)s() %(message)s"
        },
        "full": {
            "format": "%(asctime)s %(name)s %(levelname)s %(args)s %(funcName)s():%(lineno)s - %(message)s",
            'datefmt': '%Y%m%d %H:%M:%S'
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "full",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "full",
            "filename": "/tmp/fdi.log",
            "maxBytes": 20000000,
            "backupCount": 3
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"],
    },
    'disable_existing_loggers': False
}
