"""
Module provides access to logger.

This needs to be used sparingly, prefer to raise specific exceptions instead.
"""
import sys

from loguru import logger

config = {
    "handlers": [
        {
            "sink": sys.stdout,
            "format": """
-------------------------------------------------------
<level>{level}</level>
-------
TIME: <green>{time}</green>
FILE: {name}:L{line} <blue>{function}(...)</blue>
<level>{message}</level>
-------------------------------------------------------
""",
            "colorize": True,
        },
        {
            "sink": "file.log",
            "rotation": "500MB",
            "retention": "10 days",
            "format": "{time} {level} -\n{message}\n--------------------\n",
        },
    ]
}

logger.configure(**config)
logger.enable(__name__)
