"""
.. _duration_entity:
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import Any, Dict

import attr

from dialogy.types.entity import BaseEntity


@attr.s
class DurationEntity(BaseEntity):
    """Location Entity Type

    Use this type for handling locations available with reference-ids.
    This is not meant for (latitude, longitude) values, those will be covered in GeoPointEntity.
    """

    normalized = attr.ib(type=Dict[str, Any], default=attr.Factory(dict))
    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
