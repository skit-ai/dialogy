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

from typing import Any, Dict, List, Optional, Union

import attr

from dialogy import constants as const
from dialogy.types import BaseEntity, Intent

JSON_LIST_TYPE = List[Dict[str, Any]]
ORIGINAL_INTENT_TYPE = Dict[str, Union[str, float]]


@attr.frozen
class Output:
    """
    Represents output of the SLU API.
    """

    intents: List[Intent] = attr.ib(default=attr.Factory(list), kw_only=True)
    """
    A list of intents. Produced by :ref:`XLMRMultiClass <XLMRMultiClass>`
    or :ref:`MLPMultiClass <MLPMultiClass>`.
    """

    entities: List[BaseEntity] = attr.ib(default=attr.Factory(list), kw_only=True)
    """
    A list of entities. Produced by :ref:`DucklingPlugin <DucklingPlugin>`, 
    :ref:`ListEntityPlugin <ListEntityPlugin>` or :ref:`ListSearchPlugin <ListSearchPlugin>`.
    """

    original_intent: ORIGINAL_INTENT_TYPE = attr.ib(
        default=attr.Factory(dict), kw_only=True
    )

    @intents.validator  # type: ignore
    def _are_intents_valid(
        self, _: attr.Attribute, intents: List[Intent]  # type: ignore
    ) -> None:
        if not isinstance(intents, list):
            raise TypeError(f"intents must be a list, not {type(intents)}")

        if not intents:
            return

        if any(not isinstance(intent, Intent) for intent in intents):
            raise TypeError(
                f"intents must be a List[Intent] but {intents} was provided."
            )

    @entities.validator  # type: ignore
    def _are_entities_valid(
        self, _: attr.Attribute, entities: List[BaseEntity]  # type: ignore
    ) -> None:
        if not isinstance(entities, list):
            raise TypeError(f"entities must be a list, not {type(entities)}")

        if not entities:
            return

        if any(not isinstance(entity, BaseEntity) for entity in entities):
            raise TypeError(
                f"intents must be a List[BaseEntity] but {entities} was provided."
            )

    @original_intent.validator  # type: ignore
    def _is_original_intent_valid(
        self, _: attr.Attribute, original_intent: Dict[str, Union[str, float]]  # type: ignore
    ) -> None:
        if not original_intent:
            return
        if not isinstance(original_intent, dict):
            raise TypeError(
                f"original_intent must be a dict, not {type(original_intent)}"
            )
        if const.NAME not in original_intent:
            raise TypeError(
                f"original_intent must contain {const.NAME} but {original_intent} was provided."
            )
        if not isinstance(original_intent[const.NAME], str):
            raise TypeError(
                f"original_intent[{const.NAME}] must be a str, not {type(original_intent[const.NAME])}"
            )
        if const.SCORE not in original_intent:
            raise TypeError(
                f"original_intent must contain {const.SCORE} but {original_intent} was provided."
            )
        if not isinstance(original_intent[const.SCORE], float):
            raise TypeError(
                f"original_intent[{const.SCORE}] must be a float, not {type(original_intent[const.SCORE])}"
            )

    def json(self: Output) -> Dict[str, Union[JSON_LIST_TYPE, ORIGINAL_INTENT_TYPE]]:
        """
        Serialize `Output`_ to a JSON-like dict.

        :param self: [description]
        :type self: Output
        :return: [description]
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        return {
            const.INTENTS: [intent.json() for intent in self.intents],
            const.ENTITIES: [entity.json() for entity in self.entities],
            const.ORIGINAL_INTENT: self.original_intent,
        }

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
            return attr.evolve(reference, **d)
        return attr.evolve(cls(), **d)
