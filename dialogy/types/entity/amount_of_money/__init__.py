"""
.. _CurrencyEntity

Currency Entity
===============

Provides the entity class for currency values expressed in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["amount-of-money"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("five dollars is 5 dollars.")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["amount-of-money"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances="five dollars and 25 cents."))

    In [5]: output

"""
from __future__ import annotations

from typing import Any, Dict

import attr

from dialogy import constants as const
from dialogy.types.entity.numerical import NumericalEntity


@attr.s
class CurrencyEntity(NumericalEntity):
    """
    """

    unit: str = attr.ib(validator=attr.validators.instance_of(str), kw_only=True)
    entity_type: str = attr.ib(
        default="amount-of-money",
        validator=attr.validators.instance_of(str),
        kw_only=True,
    )

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
            unit=d[const.VALUE][const.UNIT],
        )
