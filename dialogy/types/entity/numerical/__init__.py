"""
.. _numerical_entity:
Module provides access to entity types that can be parsed to obtain numeric values.

Import classes:
    - NumericalEntity
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity import BaseEntity


@attr.s
class NumericalEntity(BaseEntity):
    """
    Numerical Entity Type

    Use this type for handling all entities that can be parsed to obtain:
    - numbers
    - date
    - time
    - datetime

    Attributes:
        - `dim` dimension of the entity from duckling parser
        - `type` is the type of the entity which can have values in ["value", "interval"]
    """

    origin = attr.ib(
        type=str, default="value", validator=attr.validators.instance_of(str)
    )
    entity_type: Optional[str] = attr.ib(default="number", order=False)

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int
    ) -> NumericalEntity:
        value = d[const.VALUE][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            values=[{const.VALUE: value}],
            latent=d[const.LATENT],
        )
