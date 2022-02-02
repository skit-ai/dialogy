import pytz
from typing import Callable
from datetime import datetime


def make_unix_ts(tz: str = "UTC") -> Callable[[str], int]:
    """
    Convert date in ISO 8601 format to unix ms timestamp.

    :param tz: [description], defaults to "UTC"
    :type tz: Optional[str], optional
    :return: [description]
    :rtype: Callable[[str], int]
    """
    def make_tz_aware(date_string: str) -> int:
        """
        Convert date in ISO 8601 format to unix ms timestamp.

        :param date_string: [description]
        :type date_string: str
        :return: [description]
        :rtype: int
        """
        dt = datetime.fromisoformat(date_string)
        if dt.tzinfo is None and tz not in pytz.all_timezones:
            raise ValueError(f"Invalid timezone {tz} pick from:\n{pytz.all_timezones}")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.timezone(tz))
        return int(dt.timestamp() * 1000)
    return make_tz_aware
