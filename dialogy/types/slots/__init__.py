"""
Type definition for Slots.

Import classes:

    - Slot
"""

from typing import List, Dict

import attr

from dialogy.types.entity import BaseEntity


@attr.s
class Slot:
    """Slot Type

    Keys are:
    - `name` of the slot
    - `type` is a list of types that can fill this slot
    - `values` list of entities extracted
    """

    name = attr.ib(type=str)
    type = attr.ib(type=List[str])
    values = attr.ib(type=List[BaseEntity])

    def add(self, entity: BaseEntity) -> "Slot":
        """
        Insert the `BaseEntity` within the current `Slot` instance.
        """
        self.values.append(entity)
        return self

    def clear(self) -> "Slot":
        """
        Remove all `BaseEntity` within the current `Slot` instance.
        """
        self.values = []
        return self


Rule = Dict[str, Dict[str, Dict[str, str]]]
