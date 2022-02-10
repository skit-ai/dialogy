"""
.. _people_entity:
Module provides access to entity types that can be parsed to obtain numeric values specific to denote people.

Import classes:
    - PeopleEntity
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.numerical_entity import NumericalEntity


@attr.s
class PeopleEntity(NumericalEntity):
    """
    A variant of numerical entity which addresses collections of people.

    Example sentences that contain the entity are:
    - "N people", where N is a whole number.
    - "A couple" ~ 2 people.
    - "I have triplets" ~ 3 children.
    """

    unit = attr.ib(type=str, default="", validator=attr.validators.instance_of(str))
    entity_type: Optional[str] = attr.ib(default="people", order=False)

    @classmethod
    def from_duckling(cls, d: Dict[str, Any], alternative_index: int) -> PeopleEntity:
        value = d[const.VALUE][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=[{const.VALUE: value}],
            unit=d[const.VALUE][const.UNIT],
        )
