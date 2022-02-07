from datetime import datetime
from typing import Callable, Union

import pytz


def is_unix_ts(ts: int) -> bool:
    """
    Check if the input is a unix timestamp.

    :param ts: A unix timestamp (13-digit).
    :type ts: int
    :return: True if :code:`ts` is a unix timestamp, else False.
    :rtype: bool
    """
    try:
        datetime.fromtimestamp(ts / 1000)
        return True
    except ValueError:
        return False


def dt2timestamp(date_time: datetime) -> int:
    """
    Converts a python datetime object to unix-timestamp.

    :param date_time: An instance of datetime.
    :type date_time: datetime
    :return: Unix timestamp integer.
    :rtype: int
    """
    return int(date_time.timestamp() * 1000)


def make_unix_ts(tz: str = "UTC") -> Callable[[str], int]:
    """
    Convert date in ISO 8601 format to unix ms timestamp.

    :param tz: A timezone string, defaults to "UTC"
    :type tz: Optional[str], optional
    :return: A callable that converts a date in ISO 8601 format to unix ms timestamp.
    :rtype: Callable[[str], int]
    """

    def make_tz_aware(date_string: Union[str, int]) -> int:
        """
        Convert date in ISO 8601 format to unix ms timestamp.

        :param date_string: A date in ISO 8601 format.
        :type date_string: str
        :return: A unix timestamp (13 digit).
        :rtype: int
        """
        if isinstance(date_string, int):
            return date_string
        dt = datetime.fromisoformat(date_string)
        if dt.tzinfo is None and tz not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone {tz} pick from:\n{pytz.all_timezones}")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.timezone(tz))
        return dt2timestamp(dt)

    return make_tz_aware
