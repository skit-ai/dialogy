"""
.. _time_entity:
Module provides access to entity types that can be parsed to obtain datetime values.

Import classes:
    - TimeEntity
"""
from datetime import datetime
from typing import Any, Dict, Optional

import attr
import pydash as py_  # type: ignore

from dialogy import constants as const
from dialogy.types.entity.numerical_entity import NumericalEntity


@attr.s
class TimeEntity(NumericalEntity):
    """
    Entities that can be parsed to obtain date, time or datetime values.

    Example sentences that contain the entity are:
    - "I have a flight at 6 am."
    - "I have a flight at 6th December."
    - "I have a flight at 6 am today."

    Attributes:
    - `grain` tells us the smallest unit of time in the utterance
    """

    dim = "time"
    grain = attr.ib(type=str, default=None, validator=attr.validators.instance_of(str))
    __properties_map = const.TIME_ENTITY_PROPS

    @classmethod
    def reshape(cls, dict_: Dict[str, Any]) -> Dict[str, Any]:
        dict_ = super(TimeEntity, cls).reshape(dict_)
        # Pulling out the value of entity's **grain**. The value of **grain** helps
        # us understand the precision of the entity. Usually present for `Time` dimension
        # expect "year", "month", "day", etc.
        if all(
            const.EntityKeys.GRAIN in value for value in dict_[const.EntityKeys.VALUES]
        ):
            dict_[const.EntityKeys.GRAIN] = dict_[const.EntityKeys.VALUES][0][
                const.EntityKeys.GRAIN
            ]
        return dict_

    def get_date_value(self, date: Dict[str, str]) -> Optional[str]:
        """
        Return the date string in ISO format from the dictionary passed

        .. code-block:: python

            date = {
                "value": "2021-04-17T16:00:00.000+05:30",
                "grain": "hour",
                "type": "value"
            }

        :param date: Dictionary which stores the datetime in ISO format, grain and type
        :type date: Dict[str, str]
        :return: :code:`date["value"]`
        :rtype: Optional[str]
        """
        if date.get("value"):
            return date["value"]
        else:
            raise KeyError(f"Expected key `value` in {date} for {self}")

    def is_uniq_date_from_values(self) -> bool:
        """
        Check a list has a unique day

        Where day is the date number for a month.
        Ex: for "2021-04-17T16:00:00.000+05:30", the day is 17

        .. ipython :: python

            from dialogy.types import TimeEntity
            duckling_time_entity = {
                "body": "july 19",
                "start": 0,
                "value": {
                "values": [
                    {
                    "value": "2021-07-19T00:00:00.000+05:30",
                    "grain": "day",
                    "type": "value"
                    },
                    {
                    "value": "2022-07-19T00:00:00.000+05:30",
                    "grain": "day",
                    "type": "value"
                    },
                    {
                    "value": "2023-07-19T00:00:00.000+05:30",
                    "grain": "day",
                    "type": "value"
                    }
                ],
                "value": "2021-07-19T00:00:00.000+05:30",
                "grain": "day",
                "type": "value"
                },
                "end": 7,
                "dim": "time",
                "latent": False
            }
            time_entity = TimeEntity.from_dict(duckling_time_entity)
            time_entity.is_uniq_date_from_values()


        :return: True if there is a unique day in all datetime values
        :rtype: bool
        """
        dates = []
        for date_value in self.values:
            date_ = self.get_date_value(date_value)
            if date_:
                dates.append(datetime.fromisoformat(date_).day)
        return len(py_.uniq(dates)) == 1

    def is_uniq_day_from_values(self) -> bool:
        """
        Check a list has a unique weekday

        Where weekday ranges from 0 for Monday till 6 for Sunday
        Ex: for "2021-04-17T16:00:00.000+05:30", the weekday is 5 (Saturday)

        :return: True if there is a unique weekday in all datetime values
        :rtype: bool
        """
        dates = []
        for date_value in self.values:
            date_ = self.get_date_value(date_value)
            if date_:
                dates.append(datetime.fromisoformat(date_))
        # Duckling may return 3 datetime values in chronological order.
        # For cases where someone has said "Monday", we will get 3 values,
        # each value a week apart.
        # We are pairing these dates and checking whether the difference is a week (7 days).
        # For example, if our dates are [21-04-2021, 28-04-2021, 05-05-2021],
        # then we generate pairs as (21-04-2021, 28-04-2021) and (28-04-2021, 05-05-2021).
        # If the difference between these dates is divisible by seven,
        # then we are clear that the input was a weekday.
        if not dates:
            return False
        return all(
            abs((next - prev).days) % 7 == 0
            for (prev, next) in zip(dates[:-1], dates[1:])
        )

    def set_entity_type(self) -> str:
        """
        Returns the type for this entity

        To pinpoint a time for any action, we need both DATE (either explicit or inferred) and TIME.
        We can get these in 3 possible manners:

        - both DATE and TIME, the entity type here will be DATETIME
            - Positive examples: tonight, tomorrow 4pm, 7th april 2019 6pm, last 3 hours (Because it tells us about the date as well, that is today)
            - Negative examples: Yesterday I went to park at 3pm (because the user did not say yesterday and 3pm together)
        - only DATE, the entity type here will be DATE
            - Positive examples: last month, last year, last 3 months, last 6 months, tomorrow, 27th oct 1996, 1st October 2019 till yesterday, yesterday, today, tomorrow, October, 2019, 27th October 1996 to 29th October 1996 etc
            - Negative examples: month, year, 6 months, 3 months (Since these do not have a fixed start and end date, it could have been 6 months from today, 6 months from tomorrow, previous 6 months. Therefore it only tells us a duration.)
        - only TIME, the entity type here will be TIME
            - Positive examples: 3pm, 5pm, night, morning, etc
            - Negative examples: tonight (because the date part today is in it), tomorrow night, 6th April 5pm, 7 hours (duration because they didn't mention a start/end time. It could be 7 hours from any time) etc

        if we get the grain as one of ("day", "week", "month", "quarter", "year"),
        then the entity type is DATE
        if we get grain as one of ("hour", "second", "minute") and we only have 1 value in `self.values`,
        then the entity type is DATETIME.
        if we get grain as one of ("hour", "second", "minute") and we have either a unique date or a unique weekday,
        then the entity type is DATETIME.
        else the entity type is TIME.

        :return: one of (date, time, datetime)
        :rtype: str
        """
        if self.grain in const.DATE_UNITS:
            return const.DATE
        elif self.grain in const.TIME_UNITS and len(self.values) == 1:
            return const.DATETIME
        elif self.is_uniq_date_from_values() or self.is_uniq_day_from_values():
            return const.DATETIME
        elif len(self.values) > 0:
            return const.TIME
        else:
            raise ValueError(f"Expected at least 1 value in {self.values} for {self}")

    def __attrs_post_init__(self) -> None:
        self.post_init()

    def post_init(self) -> None:
        grain_: Optional[str] = None
        if isinstance(self.values, list) and self.values:
            self.grain = self.values[0].get("grain") or self.grain
        self.entity_type = self.set_entity_type()
        self.type = self.entity_type
