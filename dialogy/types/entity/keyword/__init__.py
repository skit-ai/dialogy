"""
.. _keyword_entity:

Module provides access to an entity type (class) to contain keyword extraction based entites.
These entities originate from token lookups, regex, etc.

Import classes:
    - KeywordEntity
"""
from __future__ import annotations

from typing import Dict, Any

from pydantic import Field

from dialogy.types.entity.base_entity import BaseEntity


class KeywordEntity(BaseEntity):
    """
    Use this type for handling keyword based extractions where presence of specific tokens in the ASR
    is enough for detection.
    """

    _meta: Dict[str, str] = Field(default_factory=dict)

    # stores extra attributes defined by custom entities that can be later used by desiarialization methods once they have access to said entity classes
    meta: Dict[str, Any] = Field(default_factory=dict)

    def __init__(self, **data):  # type: ignore
        super().__init__(**data)
        self.meta = {k: v for k, v in data.items() if k not in self.__dict__}
