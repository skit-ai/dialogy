"""
Module provides access to entity types that can be parsed to obtain values like: numbers, date, time, datetime.

Import classes:
    - NumericalEntity
    - TimeEntity
    - TimeIntervalEntity
    - PeopleEntity
"""

from typing import Any, List, Dict, Callable

import attr

from dialogy import constants
from dialogy.types.entity import BaseEntity


@attr.s
class NumericalEntity(BaseEntity):
    """
    Numerical Entity Type

    Use this type for handling all entities that can be parsed to obtain:
    - numbers
    - date
    - time
    - datetime

    Attributes:
        - `dim` dimension of the entity from duckling parser
        - `values` values is a List which contains the actual value of the entity
        - `reader` gives the list of all functions that have changed the entity in some way
        - `type` is the type of the entity which can have values in ["value", "interval"]
    """

    values = attr.ib(type=List[Dict[str, Any]], default=attr.Factory(list))
    reader = attr.ib(type=List[Callable[[Any], Any]], default=attr.Factory(list))
    origin = attr.ib(
        type=str, default="value", validator=attr.validators.instance_of(str)
    )
    __properties_map = constants.BASE_ENTITY_PROPS


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

    grain = attr.ib(type=str, default=None, validator=attr.validators.instance_of(str))
    __properties_map = constants.TIME_ENTITY_PROPS


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
    __properties_map = constants.TIME_ENTITY_PROPS


@attr.s
class PeopleEntity(NumericalEntity):
    """
    A variant of numerical entity which addresses collections of people.

    Example sentences that contain the entity are:
    - "N people", where N is a whole number.
    - "A couple" ~ 2 people.
    - "I have triplets" ~ 3 children.
    """

    unit = attr.ib(type=str, default="", validator=attr.validators.instance_of(str))
    __properties_map = constants.PEOPLE_ENTITY_PROPS
