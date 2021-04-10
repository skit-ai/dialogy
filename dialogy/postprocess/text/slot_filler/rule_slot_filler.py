"""
.. _rule_slot_filler:

Module provides access to a rule-based :ref:`slot filler<slot_filler>`.
"""
from typing import Dict, List, Optional, Tuple

from dialogy.plugin import Plugin
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.types.slots import Rule
from dialogy.workflow import Workflow


class RuleBasedSlotFillerPlugin(Plugin):
    """
    A utility :ref:`plugin <plugin>` for `slot filling
    <https://nlpprogress.com/english/intent_detection_slot_filling.html>`._ An :ref:`Intent <intent>` may have

    Schema for rules looks like:
    .. code-block:: json

    {
        "<intent_name>": {
            "<slot_name>":"<entity_name>"
        }
    }

    Plugin signature:

    - `access(workflow) -> (Intent, List[BaseEntity])`
    - `mutate` not required since the mutation is implied through Intent structure change.

    Irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.
    """

    def __init__(
        self,
        rules: Rule,
        fill_multiple: bool = False,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
    ) -> None:
        # rules
        #
        # A `Dict` where each key is an intent name, and each value is another `Dict`,
        # in which, each key is an entity and value contains the `slot_name` and `entity_type.`
        #
        # example:
        # ```
        # rules = {"intent": {"slot_name": "entity_type"}}
        # ```
        super().__init__(access=access, mutate=mutate)
        self.rules: Rule = rules or {}

        # fill_multiple
        # A boolean value that commands the slot filler to add multiple values of the
        # same entity type within a slot.
        self.fill_multiple = fill_multiple

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
                    intent.fill_slot(entity, fill_multiple=self.fill_multiple)

                intent.cleanup()
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
