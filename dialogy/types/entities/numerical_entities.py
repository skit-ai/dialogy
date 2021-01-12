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

    type = attr.ib(
        type=str, default="value", validator=attr.validators.instance_of(str)
    )


@attr.s
class PeopleEntity(NumericalEntity):
    """
    People Entity Type

    Keys:
    - `unit` is the type of people (Ex. child, adult, male, female etc)
    """

    entity_type = attr.ib(type=str, default="people")
    unit = attr.ib(
        type=str, default=attr.Factory(str), validator=attr.validators.instance_of(str)
    )


@attr.s
class TimeEntity(NumericalEntity):
    """
    Time Entity Type

    Keys:
    - `grain` tells us whether someone is talking about date or time
    """

    entity_type = attr.ib(type=str, default="time")
    grain = attr.ib(
        type=str, default=attr.Factory(str), validator=attr.validators.instance_of(str)
    )


@attr.s
class DateEntity(NumericalEntity):
    """
    Time Entity Type

    Keys:
    - `grain` tells us whether someone is talking about date or time
    """

    entity_type = attr.ib(type=str, default="date")
    grain = attr.ib(
        type=str, default=attr.Factory(str), validator=attr.validators.instance_of(str)
    )


@attr.s
class DatetimeEntity(NumericalEntity):
    """
    Time Entity Type

    Keys:
    - `grain` tells us whether someone is talking about date or time
    """

    entity_type = attr.ib(type=str, default="datetime")
    grain = attr.ib(
        type=str, default=attr.Factory(str), validator=attr.validators.instance_of(str)
    )


@attr.s
class TimeIntervalEntity(TimeEntity):
    """
    Datetime Interval Entity Type

    Keys:
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """

    entity_type = attr.ib(type=str, default="time")
    type = attr.ib(type=str, default="interval")
    value = attr.ib(
        type=Dict[str, str],
        default=attr.Factory(Dict),
        validator=attr.validators.instance_of(Dict),
    )


@attr.s
class DateIntervalEntity(DateEntity):
    """
    Datetime Interval Entity Type

    Keys:
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """

    entity_type = attr.ib(type=str, default="date")
    type = attr.ib(type=str, default="interval")
    value = attr.ib(
        type=Dict[str, str],
        default=attr.Factory(Dict),
        validator=attr.validators.instance_of(Dict),
    )


@attr.s
class DatetimeIntervalEntity(DatetimeEntity):
    """
    Datetime Interval Entity Type

    Keys:
    - `value` is a Dictionary which has either keys 'from' and 'to' or both
    """

    entity_type = attr.ib(type=str, default="datetime")
    type = attr.ib(type=str, default="interval")
    value = attr.ib(
        type=Dict[str, str],
        default=attr.Factory(Dict),
        validator=attr.validators.instance_of(Dict),
    )
