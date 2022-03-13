"""
.. _PeopleEntity:

People Entity
==============

Provides the entity class for representing number of people in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["people"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("two kids")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["people"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances="two kids"))

    In [5]: output
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer


@EntityDeserializer.register(const.PEOPLE)
@attr.s
class PeopleEntity(BaseEntity):
    """
    A variant of numerical entity which addresses collections of people.

    Example sentences that contain the entity are:
    - "N people", where N is a whole number.
    - "A couple" ~ 2 people.
    - "I have triplets" ~ 3 children.
    """

    unit = attr.ib(type=str, default="", validator=attr.validators.instance_of(str))
    entity_type: Optional[str] = attr.ib(default=const.PEOPLE, order=False)

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int, **kwargs: Any
    ) -> PeopleEntity:
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
