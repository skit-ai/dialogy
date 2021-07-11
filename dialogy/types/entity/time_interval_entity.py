"""
.. _time_interval_entity:
Module provides access to entity types that can be parsed to obtain intervals of datetime.

Import classes:
    - TimeIntervalEntity
"""
from datetime import datetime
from typing import Any, Dict, Optional

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
    __properties_map = const.TIME_ENTITY_PROPS

    @classmethod
    def reshape(cls, dict_: Dict[str, Any]) -> Dict[str, Any]:
        dict_ = super(TimeIntervalEntity, cls).reshape(dict_)
        for value in dict_[const.EntityKeys.VALUES]:
            if value[const.EntityKeys.TYPE] == const.EntityKeys.INTERVAL:
                date_range = dict_[const.EntityKeys.VALUES][0].get(
                    const.EntityKeys.FROM
                ) or dict_[const.EntityKeys.VALUES][0].get(const.EntityKeys.TO)
                if not date_range:
                    raise TypeError(f"{dict_} does not match TimeIntervalEntity format")
                dict_[const.EntityKeys.GRAIN] = date_range[const.EntityKeys.GRAIN]
                break
        return dict_

    def get_value(self, reference: Any = None) -> Any:
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
        if not reference:
            date_dict = self.value.get(const.EntityKeys.FROM) or self.value.get(
                const.EntityKeys.TO
            )
        else:
            date_dict = reference.get(const.EntityKeys.FROM) or reference.get(
                const.EntityKeys.TO
            )

        if date_dict:
            return datetime.fromisoformat(date_dict.get(const.EntityKeys.VALUE))
        elif reference.get(const.EntityKeys.VALUE):
            return datetime.fromisoformat(reference.get(const.EntityKeys.VALUE))
        else:
            raise KeyError(
                f"Expected at least 1 of `from` or `to` in {self.values} for {self}"
            )

    def set_value(self, value: Optional[Dict[str, Any]] = None) -> "TimeIntervalEntity":
        """
        Set values and value attribute.

        Args:
            value (Any): The parsed value of an entity token.

        Returns:
            None
        """
        if value is None and isinstance(self.values, list) and len(self.values) > 0:
            self.value = self.values[0]
        else:
            if value:
                if isinstance(value, dict) and (
                    const.FROM in value or const.TO in value
                ):
                    self.values = [value]
                    self.value = value
                else:
                    raise TypeError(
                        "Expected value to be a dict and look like: {'to': ...,  'from': ...}"
                        f" but {type(value)} found."
                    )
            else:
                raise TypeError(
                    "Either values should be a non empty list"
                    " or value should look like: {'to': ...,  'from': ...}"
                    f" but {type(value)} found."
                )
        return self

    def __attrs_post_init__(self) -> None:
        self.post_init()
