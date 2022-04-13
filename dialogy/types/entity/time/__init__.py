"""
.. _TimeEntity:

Time Entity
============

Provides the entity class for representing time in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("tomorrow")

    In [4]: duckling_plugin.parse("monday")

    In [7]: duckling_plugin.parse("27th jan")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances=["tomorrow", "monday", "27th jan"]))

    In [5]: output
"""
from __future__ import annotations

import operator
from datetime import datetime
from typing import Any, Dict, List, Optional

import attr
import pydash as py_

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer


@EntityDeserializer.register(const.TIME)
@attr.s
class TimeEntity(BaseEntity):
    """
    Entities that can be parsed to obtain date, time or datetime values.

    Example sentences that contain the entity are:
    - "I have a flight at 6 am."
    - "I have a flight at 6th December."
    - "I have a flight at 6 am today."

    Attributes:
    - `grain` tells us the smallest unit of time in the utterance
    """

    origin: str = attr.ib(default=const.VALUE)
    dim: str = attr.ib(default=const.TIME)
    grain: str = attr.ib(default=None, validator=attr.validators.instance_of(str))
    __TIMERANGE_OPERATION_ALIAS: Dict[str, Any] = {
        const.LTE: operator.le,
        const.GTE: operator.ge,
    }

    def get_value(self) -> Any:
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
        :rtype: Optional[datetime]
        """
        entity_date_value = super().get_value()
        return datetime.fromisoformat(entity_date_value)

    def collect_datetime_values(self) -> List[datetime]:
        """
        Collect all datetime values from the entity

        :return: List of datetime values
        :rtype: List[str]
        """
        return [datetime.fromisoformat(value[const.VALUE]) for value in self.values]

    def is_uniq_date_from_values(self) -> bool:
        """
        Check a list has a unique day

        Where day is the date number for a month.

        :return: True if there is a unique day in all datetime values
        :rtype: bool
        """
        dates = self.collect_datetime_values()
        return len(py_.uniq(dates)) == 1

    def is_uniq_day_from_values(self) -> bool:
        """
        Check a list has a unique weekday

        Where weekday ranges from 0 for Monday till 6 for Sunday
        Ex: for "2021-04-17T16:00:00.000+05:30", the weekday is 5 (Saturday)

        Duckling may return 3 datetime values in chronological order. For cases where the utterance is "Monday",
        (or any weekday for that matter) we will get 3 values, each value a week apart.
        We pair these dates and check the difference is 1 week long (7 days).

        For example:

        .. code-block:: python

            # Say, our 3 date values are:
            date values = [21-04-2021, 28-04-2021, 05-05-2021]

            # then we generate pairs as:
            [(21-04-2021, 28-04-2021), (28-04-2021, 05-05-2021)]

        If the difference between these dates is divisible by seven, then the input was a weekday.

        :return: True if there is a unique weekday in all datetime values
        :rtype: bool
        """
        dates = self.collect_datetime_values()
        return all(
            abs((next - prev).days) % 7 == 0
            for (prev, next) in zip(dates[:-1], dates[1:])
        )

    def set_entity_type(self) -> None:
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
            self.entity_type = const.DATE
        elif self.grain in const.TIME_UNITS and len(self.values) == 1:
            self.entity_type = const.DATETIME
        elif self.is_uniq_date_from_values() or self.is_uniq_day_from_values():
            self.entity_type = const.DATETIME
        elif len(self.values) > 0:
            self.entity_type = const.TIME

    @classmethod
    def pick_value(
        cls, d_values: List[Dict[str, Any]], grain: str, constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        is_time = grain in const.TIME_UNITS
        constraint = constraints.get(const.TIME)
        if not is_time or not constraint:
            return d_values

        opt_items = [
            (cls.__TIMERANGE_OPERATION_ALIAS.get(opt), measure)
            for opt, measure in constraint.items()
        ]

        constrained_d_values = []
        for datetime_val in d_values:
            datetime_ = datetime.fromisoformat(datetime_val[const.VALUE])
            if all(
                opt(getattr(datetime_, const.HOUR), measure[const.HOUR])
                for opt, measure in opt_items
                if opt
            ):
                constrained_d_values.append(datetime_val)
        return constrained_d_values

    @classmethod
    def from_duckling(
        cls,
        d: Dict[str, Any],
        alternative_index: int,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> TimeEntity:
        datetime_values = d[const.VALUE][const.VALUES]
        grain = datetime_values[0][const.GRAIN]

        if constraints:
            datetime_values = cls.pick_value(
                d_values=datetime_values,
                grain=grain,
                constraints=constraints,
            )

        time_entity = cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=datetime_values,
            grain=grain,
        )
        time_entity.set_entity_type()
        return time_entity
