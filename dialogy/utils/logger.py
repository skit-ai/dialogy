"""
Setup coloredlogs
"""
import os
import logging
import coloredlogs


log = logging.getLogger("Dialogy")
fmt = "%(asctime)s:%(msecs)03d %(name)s [%(filename)s:%(lineno)s] %(levelname)s %(message)s"
coloredlogs.install(level=logging.ERROR, logger=log, fmt=fmt)


def change_log_level(level):
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)
