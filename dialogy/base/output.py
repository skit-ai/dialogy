from __future__ import annotations
from typing import List

import attr

from dialogy.types import BaseEntity, Intent


@attr.frozen
class Output:
    intents: List[Intent] = attr.ib(validator=attr.validators.instance_of(list), default=attr.Factory(list), kw_only=True)
    entities: List[BaseEntity] = attr.ib(validator=attr.validators.instance_of(list), default=attr.Factory(list), kw_only=True)

    def json(self: Output) -> dict:
        return attr.asdict(self)
