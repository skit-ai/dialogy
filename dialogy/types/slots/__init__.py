"""Slot Type"""

from typing import List

import attr

from dialogy.types.entities import BaseEntity


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

    @classmethod
    def fill(cls, entity: BaseEntity) -> "Slot":
        return cls(name=entity.slot_name, type=[entity.type], values=[entity])

    def add(self, entity: BaseEntity) -> "Slot":
        self.values.append(entity)
        return self
