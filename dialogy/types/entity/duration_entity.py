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
    """
    This entity type expects a normalized attribute. This provides the duration normalized to seconds.

    Helpful in cases where we wish to operate on time like:
    "I want a booking in 2 days."

    We can tell the time at which the sentence was said, but we need to make the booking after two days.

    This entity parses this information and also provides us the number of seconds to add to the current timestamp
    to get to a date that's 2 days ahead.
    """

    normalized = attr.ib(type=Dict[str, Any], default=attr.Factory(dict))
    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
