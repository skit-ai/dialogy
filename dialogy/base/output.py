from __future__ import annotations

from typing import Any, Dict, List, Optional

import attr

from dialogy.types import BaseEntity, Intent


@attr.frozen
class Output:
    """
    Represents outputs from a :ref:`Workflow <WorkflowClass>`.

    .. _Output:

    This is a frozen class, which means items cannot be modified once created.
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

    def json(self: Output) -> Dict[str, List[Dict[str, Any]]]:
        """
        Serialize `Output`_ to a JSON-like dict.

        :param self: [description]
        :type self: Output
        :return: [description]
        :rtype: Dict[str, List[Dict[str, Any]]]
        """
        return {
            "intents": [intent.json() for intent in self.intents],
            "entities": [entity.json() for entity in self.entities],
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
