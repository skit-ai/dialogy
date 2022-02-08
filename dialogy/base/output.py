from __future__ import annotations

from typing import Any, Dict, List, Optional

import attr

from dialogy.types import BaseEntity, Intent


@attr.frozen
class Output:
    intents: List[Intent] = attr.ib(default=attr.Factory(list), kw_only=True)
    entities: List[BaseEntity] = attr.ib(default=attr.Factory(list), kw_only=True)
    @intents.validator # type: ignore
    def _are_intents_valid(
        self,
        _: attr.Attribute, # type: ignore
        intents: List[Intent]
    ) -> None:
        if not isinstance(intents, list):
            raise TypeError(f"intents must be a list, not {type(intents)}")

        if not intents:
            return

        if any(not isinstance(intent, Intent) for intent in intents):
            raise TypeError(f"intents must be a List[Intent] but {intents} was provided.")

    @entities.validator # type: ignore
    def _are_entities_valid(
        self,
        _: attr.Attribute,  # type: ignore
        entities: List[BaseEntity]
    ) -> None:
        if not isinstance(entities, list):
            raise TypeError(f"entities must be a list, not {type(entities)}")

        if not entities:
            return

        if any(not isinstance(entity, BaseEntity) for entity in entities):
            raise TypeError(f"intents must be a List[BaseEntity] but {entities} was provided.")

    def json(self: Output) -> Dict[str, List[Dict[str, Any]]]:
        return {
            "intents": [intent.json() for intent in self.intents],
            "entities": [entity.json() for entity in self.entities],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any], reference: Optional[Output] = None) -> Output:
        if reference:
            return attr.evolve(reference, **d)
        return attr.evolve(cls(), **d)
