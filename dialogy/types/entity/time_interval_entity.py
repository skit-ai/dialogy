"""
.. _time_interval_entity:
Module provides access to entity types that can be parsed to obtain intervals of datetime.

Import classes:
    - TimeIntervalEntity
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional, List

import attr

from dialogy import constants as const
from dialogy.types.entity import TimeEntity


@attr.s
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
    value_keys = {const.FROM, const.TO, const.TYPE}
    type: str = attr.ib(default="value", order=False)
    from_value: Optional[datetime] = attr.ib(default=None, order=False)
    to_value: Optional[datetime] = attr.ib(default=None, order=False)
    values: List[Dict[str, Any]] = attr.ib(default=None, kw_only=True)
    value: Dict[str, Any] = attr.ib(default=None, kw_only=True)

    @values.validator # type: ignore
    def _check_values(
        self,
        attribute: attr.Attribute, # type: ignore
        values: List[Dict[str, Any]]
    ) -> None:
        if not values:
            return
        for value in values:
            obj_keys = set(value.keys())
            if not obj_keys.issubset(self.value_keys):
                raise TypeError(f"Expected {obj_keys} to be a subset of {self.value_keys} for {attribute.name}")

    def __attrs_post_init__(self) -> None:
        if self.values and not self.value:
            self.from_value = self.values[0].get(const.FROM, {}).get(const.VALUE)
            self.to_value = self.values[0].get(const.TO, {}).get(const.VALUE)
            self.value = {
                const.FROM: self.from_value,
                const.TO: self.to_value
            }
        elif self.value and not self.values:
            self.from_value = self.value.get(const.FROM, {})
            self.to_value = self.value.get(const.TO, {})
            self.values = [{
                const.FROM: {const.VALUE: self.from_value},
                const.TO: {const.VALUE: self.to_value}
            }]

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

        print(self.value)
        if value:
            return datetime.fromisoformat(value)
        else:
            raise KeyError(
                f"Expected at least 1 of `from` or `to` in {self.values} for {self}"
            )

    @classmethod
    def from_duckling(cls, d: Dict[str, Any], alternative_index: int) -> TimeEntity:
        from_value = d[const.VALUE].get(const.FROM)
        to_value = d[const.VALUE].get(const.TO)
        grain_source = from_value or to_value
        grain = grain_source.get(const.GRAIN)
        time_interval_entity = cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=d[const.VALUE][const.VALUES],
            type=d[const.VALUE][const.TYPE],
            grain=grain
        )
        time_interval_entity.set_entity_type()
        return time_interval_entity
