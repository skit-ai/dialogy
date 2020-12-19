"""
Slot Type
"""

from typing import List

import attr

from dialogy.types.entities import BaseEntity

@attr.s
class Slot:
    """
    Slot Type
    """
    name = attr.ib(type=str)
    type = attr.ib(type=List[str])
    values = attr.ib(type=List[BaseEntity])
