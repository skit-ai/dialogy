"""
.. _pincode_entity:

Use this type to handle all entities that can be used to obtain pincode

Import classes:
    - PincodeEntity
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer


@EntityDeserializer.register(const.PINCODE)
@attr.s
class PincodeEntity(BaseEntity):
    dim: str = attr.ib(default="pincode", kw_only=True)
    entity_type: str = attr.ib(default="pincode", kw_only=True)

    @classmethod
    def from_pattern(
        cls, transcript: str, pincode_string: str, alternative_index: int, **kwargs: Any
    ) -> PincodeEntity:
        value = pincode_string.replace(" ", "")
        return cls(
            range={const.START: 0, const.END: len(transcript)},
            body=transcript,
            alternative_index=alternative_index,
            values=[{const.VALUE: value}],
        )
