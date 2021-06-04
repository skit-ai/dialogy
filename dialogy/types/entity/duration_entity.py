"""
.. _duration_entity:
Module provides access to an entity type (class) to handle locations.

Import classes:
    - LocationEntity
"""
from typing import Any, Dict

import attr

from dialogy import constants as const
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

    @classmethod
    def reshape(cls, dict_: Dict[str, Any]) -> Dict[str, Any]:
        """
        :type dict_: Dict[str, Any]
        """
        match_start = dict_[const.EntityKeys.START]
        match_end = dict_[const.EntityKeys.END]

        dict_[const.EntityKeys.RANGE] = {
            const.EntityKeys.START: match_start,
            const.EntityKeys.END: match_end,
        }
        # ['body', 'start', 'value', 'end', 'dim', 'latent']

        dict_[const.EntityKeys.TYPE] = dict_[const.EntityKeys.DIM]

        # This piece is a preparation for multiple entity values.
        # So, even though we are confident of the value found, we are still keeping the
        # structure.
        value = dict_[const.EntityKeys.VALUE][const.EntityKeys.NORMALIZED]
        dict_[const.EntityKeys.VALUES] = [value]

        del dict_[const.EntityKeys.START]
        del dict_[const.EntityKeys.END]
        del dict_[const.EntityKeys.VALUE]
        return dict_

    def set_value(self, value: Any = None) -> "BaseEntity":
        return super().set_value(value=value)
