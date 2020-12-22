"""
Numerical Entity Types
"""
from typing import Dict

import attr

from dialogy.types.entities import BaseEntity


@attr.s
class NumericalEntity(BaseEntity):
    """
    Numerical Entity Type

    Use this type for handling all duckling entities

    Keys:
    - `type` can be either value or interval
    """
    type = attr.ib(type=str, default='value')


@attr.s
class PeopleEntity(NumericalEntity):
    """
    People Entity Type

    Keys:
    - `unit` is the type of people (Ex. child, adult, male, female etc)
    """
    unit = attr.ib(type=str, default=attr.Factory(str))


@attr.s
class TimeEntity(NumericalEntity):
    """
    Date and Time Entity Type

    Keys:
    - `grain` tells us whether someone is talking about date or time
    """
    grain = attr.ib(type=str, default=attr.Factory(str))


@attr.s
class TimeIntervalEntity(TimeEntity):
    """
    Datetime Interval Entity Type

    Keys:
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """
    value = attr.ib(type=Dict[str, str], default=attr.Factory(Dict), validator=attr.validators.instance_of(Dict))
