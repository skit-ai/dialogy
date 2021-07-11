"""
.. _currency_entity:
Module provides access to entity types that can be parsed to currencies and their value.

Import classes:
    - CurrencyEntity
"""
import attr

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

    ...
