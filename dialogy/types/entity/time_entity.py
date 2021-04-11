"""
.. _time_entity:
Module provides access to entity types that can be parsed to obtain datetime values.

Import classes:
    - TimeEntity
"""
from typing import Optional

import attr

from dialogy import constants
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
    __properties_map = constants.TIME_ENTITY_PROPS

    def __attrs_post_init__(self) -> None:
        grain_: Optional[str] = None
        if isinstance(self.values, list) and self.values:
            grain_ = self.values[0].get("grain") or self.grain
        self.entity_type = grain_ or self.type
        self.type = grain_ or self.type
