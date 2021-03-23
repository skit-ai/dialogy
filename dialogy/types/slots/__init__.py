"""
Type definition for Slots.

Import classes:

    - Slot
"""

from typing import Any, Dict, List

import attr

import dialogy.constants as const
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

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.

        Returns:
            Dict[str, Any]
        """
        entities_json = [entity.json() for entity in self.values]
        slot_json = attr.asdict(self)
        slot_json[const.EntityKeys.VALUES] = entities_json
        return slot_json


Rule = Dict[str, Dict[str, str]]
