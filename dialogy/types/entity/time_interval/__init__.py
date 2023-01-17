"""
.. _TimeIntervalEntity:

Time Interval Entity
====================

Provides the entity class for representing time intervals in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

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

    In [3]: duckling_plugin.parse("weekend")

    In [4]: duckling_plugin.parse("between 4 to 5pm")

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

    In [4]: _, output = workflow.run(Input(utterances=["weekend", "between 4 to 5pm"]))

    In [5]: output
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import root_validator, Field

from dialogy import constants as const
from dialogy.types.entity.deserialize import EntityDeserializer
from dialogy.types.entity.time import TimeEntity


@EntityDeserializer.register(const.TIME_INTERVAL)
class TimeIntervalEntity(TimeEntity):
    """
    Entities that can be parsed to obtain date, time or datetime interval.

    - "I need a flight between 6 am to 10 am."
    - "I have a flight at 6 am to 5 pm today."

    Attributes:
    - `origin`
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """

    origin = "interval"
    dim = "time"
    value_keys = [const.FROM, const.TO, const.TYPE]
    type: str = "value"
    from_value: Optional[datetime] = None
    to_value: Optional[datetime] = None
    values: List[Dict[str, Any]] = None  # type: ignore
    value: Dict[str, Any] = None  # type: ignore

    def __init__(self, **data):  # type: ignore
        if ("values" in data and data["values"]) and (
            "value" not in data or not data["value"]
        ):
            data["from_value"] = data["values"][0].get(const.FROM, {}).get(const.VALUE)
            data["to_value"] = data["values"][0].get(const.TO, {}).get(const.VALUE)
            data["value"] = {const.FROM: data["from_value"], const.TO: data["to_value"]}
        elif ("value" in data and data["value"]) and (
            "values" not in data or not data["values"]
        ):
            data["from_value"] = data["value"].get(const.FROM, {})
            data["to_value"] = data["value"].get(const.TO, {})
            data["values"] = [
                {
                    const.FROM: {const.VALUE: data["from_value"]},
                    const.TO: {const.VALUE: data["to_value"]},
                }
            ]

        super().__init__(**data)

    @root_validator
    def check_root(cls, values):  # type: ignore
        if not values["values"]:
            return values

        for value in values["values"]:
            obj_keys = set(value.keys())
            if not obj_keys.issubset(set(values["value_keys"])):
                raise TypeError(
                    f"Expected {obj_keys} to be a subset of {values['value_keys']} for values"
                )
        return values

    def collect_datetime_values(self) -> List[datetime]:
        """
        Collect all datetime values from the entity

        :return: List of datetime values
        :rtype: List[str]
        """
        datetime_values = []
        for value in self.values:
            from_value = value.get(const.FROM, {}).get(const.VALUE)
            to_value = value.get(const.TO, {}).get(const.VALUE)
            datetime_values.append(datetime.fromisoformat(from_value or to_value))
        return datetime_values

    def get_value(self) -> Any:
        """
        Return the date string in ISO format from the dictionary passed

        .. code-block:: python

            date = {
                "from": {
                    "value": "2021-04-16T16:00:00.000+05:30",
                    "grain": "hour"
                },
                "type": "interval"
            }

        :param date: Dictionary which stores the datetime in ISO format, grain and type
        :type date: Dict[str, str]
        :return: :code:`date["value"]`
        :rtype: Optional[datetime]
        """
        value = self.value.get(const.FROM) or self.value.get(const.TO)
        if value:
            return datetime.fromisoformat(value)
        else:
            raise KeyError(
                f"Expected at least 1 of `from` or `to` in {self.values} for {self}"
            )

    @classmethod
    def pick_value(
        cls, d_values: List[Dict[str, Any]], grain: str, constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filters interval datetime values outside of timerange constraint

        Filter logic apply constraint on both "from" and "to" individually:
        - both FROM and TO present and inside constraint
            - no filtering
        - both FROM and TO present but only FROM inside constraint
            - filter TO
        - both FROM and TO present but only TO inside constraint
            - replace FROM value with constraint lowerbound datetime value
        - both FROM and TO present but outside constraint
            - filter both TO and FROM
        - only FROM present and inside constraint
            - no filtering
        - only FROM present and outside constraint
            - filter FROM

        """
        is_time = grain in const.TIME_UNITS
        constraint = constraints.get(const.TIME)
        if not is_time or not constraint:
            return d_values

        constrained_d_values = []
        for datetime_val in d_values:
            from_datetime_val = datetime_val.get(const.FROM, {})
            to_datetime_val = datetime_val.get(const.TO, {})
            from_ = from_datetime_val and cls.apply_constraint(
                datetime.fromisoformat(from_datetime_val.get(const.VALUE)),
                constraint,
            )
            to_ = to_datetime_val and cls.apply_constraint(
                datetime.fromisoformat(to_datetime_val.get(const.VALUE)),
                constraint,
            )

            if from_ and to_:
                constrained_d_values.append(datetime_val)
            elif from_:
                constrained_d_values.append(
                    {
                        const.FROM: datetime_val.get(const.FROM),
                        const.TYPE: datetime_val.get(const.TYPE),
                    }
                )
            elif to_:
                from_or_to = const.FROM if from_datetime_val else const.TO
                gte_or_lte = const.GTE if from_datetime_val else const.LTE
                datetime_val[from_or_to][const.VALUE] = (
                    datetime.fromisoformat(
                        datetime_val.get(from_or_to, {}).get(const.VALUE)
                    )
                    .replace(
                        hour=constraint[gte_or_lte][const.HOUR],
                        minute=constraint[gte_or_lte][const.MINUTE],
                        second=0,
                        microsecond=0,
                    )
                    .isoformat()
                )
                constrained_d_values.append(datetime_val)

        return constrained_d_values

    @classmethod
    def from_duckling(
        cls,
        d: Dict[str, Any],
        alternative_index: int,
        constraints: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> TimeEntity:
        from_value = d[const.VALUE].get(const.FROM)
        to_value = d[const.VALUE].get(const.TO)
        grain_source = from_value or to_value
        grain = grain_source.get(const.GRAIN)

        datetime_values = d[const.VALUE][const.VALUES]

        if constraints:
            datetime_values = cls.pick_value(
                d_values=datetime_values,
                grain=grain,
                constraints=constraints,
            )

        time_interval_entity = cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=datetime_values,
            type=d[const.VALUE][const.TYPE],
            grain=grain,
        )
        time_interval_entity.set_entity_type()
        return time_interval_entity
