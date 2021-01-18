"""
Module provides access to logger.

This needs to be used sparingly, prefer to raise specific exceptions instead.

Import functions:
    - change_log_level
"""
import logging
import coloredlogs


log = logging.getLogger("Dialogy")
fmt = "%(asctime)s:%(msecs)03d %(name)s [%(filename)s:%(lineno)s] %(levelname)s %(message)s"
coloredlogs.install(level=logging.ERROR, logger=log, fmt=fmt)


def change_log_level(level: str) -> None:
    """
    Change log level throughout the project.

    Args:
        level (str): One of: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    log.setLevel(level)
    for handler in log.handlers:
        handler.setLevel(level)
