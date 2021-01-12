"""
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import List, Dict

import attr

from dialogy.types.entities import BaseEntity


@attr.s
class LocationEntity(BaseEntity):
    """
    Location Entity Type

    The keys are the same as Base Entity.

    Keys:
    - `value` is an integer that is the index of the location in the knowledge base
    """
    values = attr.ib(
        type=List[Dict[str, int]],
        default=attr.Factory(List),
        validator=attr.validators.instance_of(List),
    )
    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(Dict))
