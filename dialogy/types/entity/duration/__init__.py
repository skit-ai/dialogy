"""
.. _DurationEntity:

Duration Entity
================

Provides the entity class for durations in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["duration"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("she said 2h.")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["duration"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances="she said 2h"))

    In [5]: output
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types import BaseEntity


@attr.s
class DurationEntity(BaseEntity):
    """
    This entity type expects a normalized attribute. This provides the duration normalized to seconds.

    Helpful in cases where we wish to operate on time like:
    "I want a booking in 2 days."

    We can tell the time at which the sentence was said, but we need to make the booking after two days.

    This entity parses this information and also provides us the number of seconds to add to the current timestamp
    to get to a date that's 2 days ahead.
    """

    unit: str = attr.ib(validator=attr.validators.instance_of(str), kw_only=True)
    normalized: Dict[str, Any] = attr.ib(default=attr.Factory(dict))
    _meta: Dict[str, str] = attr.ib(default=attr.Factory(dict))
    entity_type: str = attr.ib(default="duration", kw_only=True)

    @classmethod
    def from_duckling(cls, d: Dict[str, Any], alternative_index: int) -> DurationEntity:
        value = d[const.VALUE][const.NORMALIZED][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=[{const.VALUE: value}],
            unit=d[const.VALUE][const.UNIT],
            normalized=d[const.VALUE][const.NORMALIZED],
        )
