"""
Module provides access to a rule-based slot-filler.

This is best suited for post-processing.

Consider a minimal rule schema:
```python

{
    "<intent_name>": {
        "<entity_type>": {
            "slot_name": "<slot_name>",
            "entity_name": "<entity_name>"
        } 
    }
}
```

Then irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.

Import Plugin:
    - SlotFiller
"""
from typing import Dict, List, Optional, Tuple

import attr

from dialogy.plugin import Plugin
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow


@attr.s
class RuleBasedSlotFillerPlugin(Plugin):
    """
    [summary]

    Attributes:
        - `rules` Dict[str, List[str]]: A relationship between intent and entities.
        - `slots` Dict[str, Slot]: A container for slots for a given intent.

    Raises:
        TypeError: [description]

    Returns:
        [type]: [description]
    """

    rules = attr.ib(type=Dict[str, Dict[str, str]], default=attr.Factory(Dict))

    def __call__(
        self, access: Optional[PluginFn] = None, mutate: Optional[PluginFn] = None
    ) -> PluginFn:
        def filler(workflow: Workflow) -> None:
            if access is not None:

                try:
                    intent_and_entities: Tuple[Intent, List[BaseEntity]] = access(
                        workflow
                    )
                    intent, entities = intent_and_entities
                    intent.apply(self.rules)

                    for entity in entities:
                        intent.fill_slot(entity)
                except TypeError as type_error:
                    raise TypeError(
                        f"`access` passed to {self.__class__.__name__}"
                        f" is not a Callable. Received {type(access)} instead."
                    ) from type_error
            else:
                raise TypeError(
                    f"`access` passed to {self.__class__.__name__}"
                    f" is not a Callable. Received {type(access)} instead."
                )

        return filler
