"""
Module provides access to logger.

This needs to be used sparingly, prefer to raise specific exceptions instead.

Import functions:
    - change_log_level
"""
import logging
from functools import wraps
from typing import Any, Callable, Union

import coloredlogs

log = logging.getLogger("Dialogy")
fmt = "%(asctime)s:%(msecs)03d %(name)s [%(filename)s:%(lineno)s] %(levelname)s %(message)s"
coloredlogs.install(level=logging.ERROR, logger=log, fmt=fmt)


def change_log_level(logger: logging.Logger, level: Union[str, int]) -> None:
    """
    Change log level throughout the project.

    Args:
        level (str):

    :param logger: The logger that needs to undergo logging changes.
    :type logger: logging.Logger
    :param level: One of: DEBUG, INFO, WARNING, ERROR, CRITICAL
    :type level: Union[str, int]
    :return: None
    :rtype: None
    """
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)


def dbg(logger: logging.Logger):
    """
    Change debug level briefly.

    There are methods that need debug logs but not all of them, not all the time.
    This decorator checks if it is being applied on a method or a function.

    1. If function or method, it checks the kwargs to have set a :code:`debug=True` (configurable via :code:`arg_name`).
    2. If a method without the kwargs, then it makes a check analogous to :code:`if instance.debug == True`.
    3. If either of the first two conditions pass, we change the log level to DEBUG, execute the function and change the
        log-level back to ERROR.
    4. If neither conditions pass, we run the function as it is.

    This way, we restrict debug logs to only those classes, methods and functions that need it.

    :param logger: The logger that needs to undergo logging changes.
    :type logger: logging.Logger
    :return:
    :rtype:
    """

    def wrapper(func: Callable[..., Any], arg_name="debug", attr_name="debug"):
        """
        :param func: A function or a method
        :type func: Callable[..., Any]
        :param arg_name: The name in kwargs that implies a debug flag.
        :type arg_name: str
        :param attr_name: The attribute in an instance that implies a debug flag.
        :type attr_name: str
        :return: Wrapper function
        :rtype: Callable[..., Any]
        """

        @wraps(func)
        def restrict_log_level(*args, **kwargs) -> Any:
            debug_arg = kwargs.get(arg_name, False)
            is_object = args and isinstance(args[0], object)
            debug_attr = False

            try:
                if is_object:
                    debug_attr = getattr(args[0], attr_name)
            except AttributeError:
                debug_attr = False

            if debug_arg or debug_attr:
                change_log_level(logger, logging.DEBUG)
                output = func(*args, **kwargs)
                change_log_level(logger, logging.ERROR)
            else:
                output = func(*args, **kwargs)
            return output

        return restrict_log_level

    return wrapper
