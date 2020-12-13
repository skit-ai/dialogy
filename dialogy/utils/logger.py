"""
Setup coloredlogs
"""
import logging
import coloredlogs
from typing import Union


log = logging.getLogger("Dialogy")
fmt = "%(asctime)s:%(msecs)03d %(name)s [%(filename)s:%(lineno)s] %(levelname)s %(message)s"
coloredlogs.install(level=logging.ERROR, logger=log, fmt=fmt)


def change_log_level(level: str) -> None:
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)
