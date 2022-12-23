"""
Type definition for Slots. Read :ref:`Intent<Intent>` and :ref:`Slot Filling<Slot Filling>` for details.
"""
from __future__ import annotations

from typing import Any, Dict, List

import attr

from dialogy.types import BaseEntity


@attr.s
class Slot:
    """
    Slot Type

    .. _Slot:

    Keys are:
    - `name` of the slot
    - `type` is a list of types that can fill this slot
    - `values` list of entities extracted
    """

    name: str = attr.ib(kw_only=True, order=True)
    types: List[str] = attr.ib(kw_only=True, factory=list, order=False)
    values: List[BaseEntity] = attr.ib(kw_only=True, factory=list, order=False)

    def add(self, entity: BaseEntity) -> Slot:
        """
        Insert the `BaseEntity` within the current `Slot` instance.
        """
        self.values.append(entity)
        return self

    def clear(self) -> Slot:
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
        return {
            "name": self.name,
            "types": self.types,
            "values": [entity.json() for entity in self.values],
        }


Rule = Dict[str, Dict[str, Any]]
