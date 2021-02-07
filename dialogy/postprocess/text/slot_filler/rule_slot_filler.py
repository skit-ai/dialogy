"""
Module provides access to a rule-based [SlotFiller](../__init__.html).

## Tutorials
- [RuleSlotFiller](../../../../tests/postprocess/text/slot_filler/test_rule_slot_filler.html)

Imports:

- RuleBasedSlotFillerPlugin
"""
from typing import Dict, List, Tuple

import attr

from dialogy.plugin import Plugin
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.types.slots import Rule
from dialogy.workflow import Workflow

# == RuleBasedSlotFillerPlugin ==
@attr.s
class RuleBasedSlotFillerPlugin(Plugin):
    """
    An instance of this class is used for generating a slot-filler.

    Schema for rules looks like:
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

    Plugin signature:

    - `access(workflow) -> (Intent, List[BaseEntity])`
    - `mutate` not required since the mutation is implied through Intent structure change.

    Irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.
    """

    # **rules**
    #
    # A `Dict` where each key is an intent name, and each value is another `Dict`,
    # in which, each key is an entity and value contains the `slot_name` and `entity_type.`
    #
    # example:
    # ```
    # rules = {"basic": {"slot_name": "basic_slot", "entity_type": "basic"}}
    # ```
    rules = attr.ib(type=Rule, default=attr.Factory(Dict))

    # == filler ==
    def filler(self, workflow: Workflow) -> None:
        """
        Update an intent slot with compatible entity.

        - `access(workflow)` should return a tuple. `Intent`, `List[BaseEntity]`.
        - Only 1 entity fills the slot type.

        Args:
            workflow (Workflow)

        Raises:
            TypeError: self.access should be a Callable.
        """
        if self.access is not None:

            try:
                intent_and_entities: Tuple[Intent, List[BaseEntity]] = self.access(
                    workflow
                )
                intent, entities = intent_and_entities
                intent.apply(self.rules)

                for entity in entities:
                    intent.fill_slot(entity)
            except TypeError as type_error:
                raise TypeError(
                    f"`access` passed to {self.__class__.__name__}"
                    f" is not a Callable. Received {type(self.access)} instead."
                ) from type_error
        else:
            raise TypeError(
                f"`access` passed to {self.__class__.__name__}"
                f" is not a Callable. Received {type(self.access)} instead."
            )

    # == __call__ ==
    def __call__(self) -> PluginFn:
        """
        [callable-plugin](../../../plugin/plugin.html#__call__)
        """
        return self.filler
