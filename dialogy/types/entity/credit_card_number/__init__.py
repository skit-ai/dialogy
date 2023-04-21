"""
.. _CreditCardNumberEntity

Credit Card Number Entity
=========================

Provides the entity class for credit card numbers in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["credit-card-number"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("my credit card number is 4111111111111111.")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["credit-card-number"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances="my credit card number is 4111111111111111."))

    In [5]: output

"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from dialogy import constants as const
from dialogy.types import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer


@EntityDeserializer.register(const.CREDIT_CARD_NUMBER)
class CreditCardNumberEntity(BaseEntity):
    entity_type: str = const.CREDIT_CARD_NUMBER
    issuer: Optional[str] = None
    value: str = None  # type: ignore
    values: List[Dict[str, Any]]

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int, **kwargs: Any
    ) -> CreditCardNumberEntity:
        value = d[const.VALUE][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=[{const.VALUE: value}],
            issuer=d[const.VALUE][const.ISSUER],
        )
