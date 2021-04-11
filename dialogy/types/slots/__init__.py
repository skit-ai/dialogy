"""
.. _slot:

Type definition for Slots.

Import classes:

    - Slot
"""

from typing import Any, Dict, List

import dialogy.constants as const
from dialogy.types.entity import BaseEntity


class Slot:
    """Slot Type

    Keys are:
    - `name` of the slot
    - `type` is a list of types that can fill this slot
    - `values` list of entities extracted
    """

    def __init__(self, name: str, type_: List[str], values: List[BaseEntity]) -> None:
        self.name = name
        self.type = type_
        self.values = values

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
        slot_json = {
            "name": self.name,
            "type": self.type,
            const.EntityKeys.VALUES: entities_json,
        }
        return slot_json


Rule = Dict[str, Dict[str, str]]
