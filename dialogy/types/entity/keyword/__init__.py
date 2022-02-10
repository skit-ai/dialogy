"""
.. _keyword_entity:

Module provides access to an entity type (class) to contain keyword extraction based entites.
These entities originate from token lookups, regex, etc.

Import classes:
    - KeywordEntity
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity


@attr.s
class KeywordEntity(BaseEntity):
    """
    Use this type for handling keyword based extractions where presence of specific tokens in the ASR
    is enough for detection.
    """

    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
