"""
Module provides access to entity types that can be parsed to obtain numeric values.

Import classes:
    - NumericalEntity
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
