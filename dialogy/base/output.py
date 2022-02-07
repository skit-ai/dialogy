from __future__ import annotations

from typing import Any, Dict, List, Optional

import attr

from dialogy.types import BaseEntity, Intent


@attr.frozen
class Output:
    intents: List[Intent] = attr.ib(
        validator=attr.validators.instance_of(list),
        default=attr.Factory(list),
        kw_only=True,
    )
    entities: List[BaseEntity] = attr.ib(
        validator=attr.validators.instance_of(list),
        default=attr.Factory(list),
        kw_only=True,
    )

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
