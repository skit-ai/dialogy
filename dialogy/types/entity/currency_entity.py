"""
.. _currency_entity:
Module provides access to entity types that can be parsed to currencies and their value.

Import classes:
    - CurrencyEntity
"""
from __future__ import annotations
from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.numerical_entity import NumericalEntity


@attr.s
class CurrencyEntity(NumericalEntity):
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

    unit = attr.ib(type=str, validator=attr.validators.instance_of(str), kw_only=True)
    entity_type = attr.ib(default="amount-of-money", kw_only=True)

    def get_value(self) -> Any:
        """
        Getter for CurrencyEntity.

        We are yet to decide the pros and cons of the output. It seems retaining {"value": float, "unit": }

        :param reference: [description], defaults to None
        :type reference: Any, optional
        :return: [description]
        :rtype: Any
        """
        value = super().get_value()
        return f"{self.unit}{value:.2f}"

    @classmethod
    def from_duckling(cls, d: Dict[str, Any], alternative_index: int) -> CurrencyEntity:
        value = d[const.VALUE][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            values=[{const.VALUE: value}],
            latent=d[const.LATENT],
            unit=d[const.VALUE][const.UNIT]
        )
