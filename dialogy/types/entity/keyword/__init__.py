"""
.. _CreditCardNumberEntity

Keword Entity
==============

Provides the entity class for entities generated via patterns or tokens.
This entity is obtained via :ref:`ListSearchPlugin<ListSearchPlugin>` and :ref:`ListSearchPlugin<ListSearchPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import ListEntityPlugin

    In [2]: entity_extractor = ListEntityPlugin(
       ...: dest="output.entities",
       ...: input_column="data",
       ...: output_column="entities",
       ...: use_transform=True,
       ...: style="regex",
       ...: candidates={"fruits": {"apple": [r"apples?"], "orange": [r"oranges?"]}},
       ...: )

    In [3]: entity_extractor.get_entities(["lets not compare apples to oranges!"])

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import ListEntityPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: entity_extractor = ListEntityPlugin(
       ...: dest="output.entities",
       ...: input_column="data",
       ...: output_column="entities",
       ...: use_transform=True,
       ...: style="regex",
       ...: candidates={"fruits": {"apple": [r"apples?"], "orange": [r"oranges?"]}},
       ...: )

    In [3]: workflow = Workflow([entity_extractor])

    In [4]: _, output = workflow.run(Input(utterances="lets not compare apples to oranges!"))

    In [5]: output
"""
from __future__ import annotations

from typing import Dict

import attr

from dialogy.types.entity.base_entity import BaseEntity


@attr.s
class KeywordEntity(BaseEntity):
    """
    Use this type for handling keyword based extractions where presence of specific tokens in the ASR
    is enough for detection.
    """

    _meta = attr.ib(type=Dict[str, str], default=attr.Factory(dict))
