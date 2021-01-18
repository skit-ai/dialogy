"""
Module provides access to a rule-based slot-filler.

This is best suited for post-processing.

Consider a minimal rule schema:
```yaml

intent_name: # The name of the intent
  slots:
  - name: str: str # The name of a slot.
    entity_type: str # Entity type, like: NumericalEntity, TimeEntity, etc.
    values: List[BaseEntity]
```
Then irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.

Import Plugin:
    - SlotFiller
"""
from typing import Optional, Callable, List, Dict, Any, Tuple

import attr

from dialogy.plugins import Plugin
from dialogy.types.plugins import PluginFn
from dialogy.types.intents import Intent
from dialogy.types.entities import BaseEntity
from dialogy.workflow import Workflow


@attr.s
class RuleBasedSlotFillerPlugin(Plugin):
    rules = attr.ib(type=Dict[str, Any], default=attr.Factory(Dict))

    def exec(
        self, 
        access: Optional[PluginFn] = None, 
        mutate: Optional[PluginFn] = None
    ) -> PluginFn:
        def filler(workflow: Workflow) -> None:
            slot_container = []

            if access is not None:

                intent_and_entities: Tuple[Intent, List[BaseEntity]] = access(workflow)
                confident_class = intent_and_entities[0]
                entities = intent_and_entities[1]

                # TODO: Create a type for a slot
                # TODO: Create a type for slot-filling-rules
                slots = self.rules[confident_class.name]["slots"]

                # TODO: RuleParser can check containment instead of this loop
                for entity in entities:
                    for slot in slots:
                        if entity.entity_type in slot.entity_type:
                            slot_container.append(entity)
            else:
                raise TypeError(f"`access` passed to RuleBasedSlotFillerPlugin is not a Callable. Received {type(access)} instead.")

        return filler
