"""
.. _Output:

The :ref:`Output <Output>` class creates immutable instances that describe the output of a single turn of a conversation.
The output contains 

#. :code:`List[Intent]` sorted in descending order of confidence scores.
#. :code:`List[BaseEntity]` in an arbitrary order.

We don't require the :code:`List[BaseEntity]` apart from logging purposes. We fill relevant entities within :ref:`slots <Slot>`
of the predicted :ref:`Intent<Intent>`. Currently this is done only for the :ref:`Intent<Intent>` with the highest confidence score.
That's because currently, we only process a single trigger from the SLU API (at the dialog manager), which is an :ref:`Intent<Intent>`.

.. admonition:: Why do I see :ref:`Input <Input>` and :ref:`Output <Output>` as inputs to all :ref:`Plugins <AbstractPlugin>`?

    It is a common pattern for all the plugins to require both as arguments. Since this could be confusing nomenclature, :ref:`Input <Input>`
    and :ref:`Output <Output>` bear meaning and even separation for the SLU API, **not for** :ref:`Plugins <AbstractPlugin>`.

Setting Output
--------------

Just like :ref:`Input <Input>`, :ref:`Output <Output>` is also an immutable class.

#. **Don't change the attribute elements in place.** It would work for now
   but even types like `Intent` and `BaseEntity` will soon become immutable as well.

#. Plugins that produce output must always produce a :code:`List[Intent]` or :code:`List[BaseEntity]`.
   Say, returning a single :code:`Intent` would break validations on the output class.


Serialization
-------------

If there is a need to represent an :ref:`Input<Input>` as a `dict` we can do the following:

.. ipython::

    In [1]: from dialogy.base import Output
       ...: from dialogy.types import Intent

    In [2]: output = Output(intents=[Intent(name="_greeting_", score=1.0)])

    In [3]: output.json()
"""
from __future__ import annotations

from typing import Any, Dict, List, Union, Optional

from pydantic import BaseModel, Field, validator

from dialogy import constants as const
from dialogy.types import BaseEntity, Intent
from dialogy.types.entity.deserialize import EntityDeserializer


JSON_LIST_TYPE = List[Dict[str, Any]]
ORIGINAL_INTENT_TYPE = Dict[str, Union[str, float]]


class Output(BaseModel):
    """
    Represents output of the SLU API.
    """

    intents: List[Intent] = Field(default_factory=list)
    """
    A list of intents. Produced by :ref:`XLMRMultiClass <XLMRMultiClass>`
    or :ref:`MLPMultiClass <MLPMultiClass>`.
    """

    entities: List[BaseEntity] = Field(default_factory=list)
    """
    A list of entities. Produced by :ref:`DucklingPlugin <DucklingPlugin>`, 
    :ref:`ListEntityPlugin <ListEntityPlugin>` or :ref:`ListSearchPlugin <ListSearchPlugin>`.
    """

    original_intent: ORIGINAL_INTENT_TYPE = Field(default_factory=dict)

    class Config:
        allow_mutation = False

    def __init__(self, **data: Any):
        if "entities" in data and isinstance(data["entities"], list):
            entities = [
                EntityDeserializer.deserialize_json(**ent)
                if isinstance(ent, dict)
                else ent
                for ent in data["entities"]
            ]
            data["entities"] = entities

        super().__init__(**data)

    @validator("original_intent")
    def is_original_intent_valid(cls, v):  # type: ignore
        if not v:
            return {}
        if const.NAME not in v:
            raise TypeError(
                f"original_intent must contain {const.NAME} but {v} was provided."
            )
        if not isinstance(v[const.NAME], str):
            raise TypeError(
                f"original_intent[{const.NAME}] must be a str, not {type(v[const.NAME])}"
            )
        if const.SCORE not in v:
            raise TypeError(
                f"original_intent must contain {const.SCORE} but {v} was provided."
            )

        v[const.SCORE] = float(v[const.SCORE])

        return v

    @classmethod
    def from_dict(cls, d: Dict[str, Any], reference: Optional[Output] = None) -> Output:
        """
        Create a new `Output`_ instance from a dictionary.

        :param d: A dictionary such that keys are a subset of `Output`_ attributes.
        :type d: Dict[str, Any]
        :param reference: An existing `Output`_ instance., defaults to None
        :type reference: Optional[Output], optional
        :return: A new `Output`_ instance.
        :rtype: Output
        """
        if reference:
            return reference.copy(update=d, deep=True)
        return cls(**d)
