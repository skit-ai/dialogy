"""
.. _NumericalEntity:

Numerical Entity
============

Provides the entity class for representing numbers in natural language. This entity is obtained via :ref:`DucklingPlugin<DucklingPlugin>`.

Plugin Walkthrough
------------------

.. ipython::

    In [1]: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["number"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: duckling_plugin.parse("12")

    In [4]: duckling_plugin.parse("twenty two")

Workflow Integration
--------------------

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.workflow import Workflow

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["number"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: _, output = workflow.run(Input(utterances=["seventy two", "4 fruits"]))

    In [5]: output

CASTING
--------

We have noticed that there is a need to cast numerical values to time. The :ref:`as_time<number_entity_as_time>` method can be used to do this.
The default assumption is to use the number as :code:`day` but we can also replace the :code:`month` and :code:`hour`.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.types import Intent
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["number"],
       ...:     locale="en_IN",
       ...:     timezone="Asia/Kolkata",
       ...: )

    In [3]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [4]: entities = duckling_plugin.parse("12")

    In [5]: [entity.as_time(reference_time, "Asia/Kolkata") for entity in entities]

"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

import attr

from dialogy import constants as const
from dialogy.types.entity.base_entity import BaseEntity
from dialogy.types.entity.deserialize import EntityDeserializer
from dialogy.types.entity.time import TimeEntity
from dialogy.utils import unix_ts_to_datetime


@EntityDeserializer.register(const.NUMBER)
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
    entity_type: Optional[str] = attr.ib(default=const.NUMBER, order=False)

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int, **kwargs: Any
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

    def as_time(
        self, reference_unix_ts: int, timezone: str, replace: str = "day"
    ) -> TimeEntity:
        """
        Converts a duration entity to a time entity.

        .. _number_entity_as_time:
        """
        reference_datetime: datetime = unix_ts_to_datetime(
            reference_unix_ts, timezone=timezone
        )
        if replace not in [const.HOUR, const.DAY, const.MONTH]:
            raise RuntimeError(
                f"Expected replace to be one of {[const.HOUR, const.DAY, const.MONTH]}"
            )
        value = reference_datetime.replace(**{replace: self.value}).isoformat()

        entity = TimeEntity(
            range={
                const.START: self.range[const.START],
                const.END: self.range[const.END],
            },
            body=self.body,
            score=self.score,
            dim="time",
            alternative_index=self.alternative_index,
            latent=self.latent,
            values=[{const.VALUE: value}],
            grain=replace,
        )
        entity.set_entity_type()
        return entity
