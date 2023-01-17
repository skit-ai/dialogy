"""
Type definition for Slots. Read :ref:`Intent<Intent>` and :ref:`Slot Filling<Slot Filling>` for details.
"""
from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from dialogy.types import BaseEntity


class Slot(BaseModel):
    """
    Slot Type

    .. _Slot:

    Keys are:
    - `name` of the slot
    - `type` is a list of types that can fill this slot
    - `values` list of entities extracted
    """

    name: str
    types: List[str] = Field(default_factory=list)
    values: List[BaseEntity] = Field(default_factory=list)

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


Rule = Dict[str, Dict[str, Any]]
