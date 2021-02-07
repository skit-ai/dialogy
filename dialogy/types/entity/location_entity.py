"""
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import List, Dict

import attr

from dialogy.types.entity import BaseEntity


@attr.s
class LocationEntity(BaseEntity):
    """Location Entity Type

    Use this type for handling locations available with reference-ids.
    This is not meant for (latitude, longitude) values, those will be covered in GeoPointEntity.

    Attributes:
        - `values` values is a List which contains the actual value of the entity
    """

    values = attr.ib(
        type=List[Dict[str, int]],
        default=attr.Factory(List),
        validator=attr.validators.instance_of(List),
    )
    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(Dict))
