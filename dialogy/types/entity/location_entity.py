"""
.. _location_entity:
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import Dict

import attr

from dialogy.types.entity import BaseEntity


@attr.s
class LocationEntity(BaseEntity):
    """
    Use this type for handling locations available with reference-ids.
    This is not meant for (latitude, longitude) values, those will be covered in GeoPointEntity.
    """

    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(Dict))
