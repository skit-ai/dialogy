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
    type = attr.ib(type=str, default="value",
                   validator=attr.validators.instance_of(str))


@attr.s
class PeopleEntity(NumericalEntity):
    """
    People Entity Type

    Keys:
    - `unit` is the type of people (Ex. child, adult, male, female etc)
    """
    entity_type = attr.ib(type=str, default="people")
    unit = attr.ib(type=str, default=attr.Factory(str), 
                   validator=attr.validators.instance_of(str))
