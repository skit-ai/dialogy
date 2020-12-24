"""
Location Entity Types
"""
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
    value = attr.ib(type=int, default=attr.Factory(int), validator=attr.validators.instance_of(int))
