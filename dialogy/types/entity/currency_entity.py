"""
.. _currency_entity:
Module provides access to entity types that can be parsed to currencies and their value.

Import classes:
    - CurrencyEntity
"""
from typing import Any, Dict

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

    @classmethod
    def reshape(cls, dict_: Dict[str, Any]) -> Dict[str, Any]:
        unit = dict_[const.EntityKeys.VALUE].get(const.EntityKeys.UNIT)
        dict_ = super().reshape(dict_)
        dict_[const.EntityKeys.UNIT] = unit
        return dict_

    def get_value(self, reference: Any = None) -> Any:
        """
        Getter for CurrencyEntity.

        We are yet to decide the pros and cons of the output. It seems retaining {"value": float, "unit": }

        :param reference: [description], defaults to None
        :type reference: Any, optional
        :return: [description]
        :rtype: Any
        """
        value = super().get_value(reference=reference)
        return f"{self.unit}{value:.2f}"
