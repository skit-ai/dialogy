"""
.. _time_interval_entity:
Module provides access to entity types that can be parsed to obtain intervals of datetime.

Import classes:
    - TimeIntervalEntity
"""
from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.time_entity import TimeEntity


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

    def set_value(self, value: Optional[Dict[str, Any]] = None) -> None:
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
                if (
                    isinstance(value, dict)
                    and const.TO in value
                    and const.FROM in value
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
