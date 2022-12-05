"""
.. _address_entity:
Module provides access to entity types that can be parsed via address using Gmaps or Mapmyindia.

Import classes:
    - AddressEntity
"""
from __future__ import annotations

from typing import Any

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer


@EntityDeserializer.register(const.ADDRESS)
class AddressEntity(BaseEntity):
    dim: str = "address"
    entity_type: str = "address"

    @classmethod
    def from_maps(
        cls, transcript: str, address_string: str, alternative_index: int, **kwargs: Any
    ) -> AddressEntity:
        value = address_string
        return cls(
            range={const.START: 0, const.END: len(transcript)},
            body=transcript,
            alternative_index=alternative_index,
            values=[{const.VALUE: value}],
        )
