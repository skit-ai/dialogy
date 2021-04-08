"""
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import Dict, List, Any

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


"""
{
    "body": "2 days",
    "latent": false,
    "values": [
      {
        "value": 2,
        "day": 2,
        "type": "value",
        "unit": "day",
        "normalized": {
          "value": 172800,
          "unit": "second"
        }
      }
    ],
    "type": "duration",
    "range": {
      "start": 0,
      "end": 6
    },
    "parser": "rhea",
    "alternative_index": 0
}
"""