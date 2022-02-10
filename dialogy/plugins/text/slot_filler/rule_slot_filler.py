"""
.. _rule_slot_filler:

Module provides access to a rule-based :ref:`slot filler<slot_filler>`.
"""
from typing import Any, List, Optional

from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.slots import Rule
from dialogy.utils.logger import logger


class RuleBasedSlotFillerPlugin(Plugin):
    """
    A utility :ref:`plugin <plugin>` for
    `slot filling <https://nlpprogress.com/english/intent_detection_slot_filling.html>`._
    An :ref:`Intent <intent>` may have a few slots that need to be filled.

    This plugin can assist filling pertaining to certain intent:entity:slot-name association rules.

    Schema for rules looks like:

    .. code-block:: json

        {
            "intent_name": {
                "slot_name":"entity_type"
            }
        }

    This can be represented in a yaml format like so:

    .. code-block:: yaml

        slots:
            faqs:
                action_slot: actions
            report:
                time_slot:
                - time
                - number

    Let's run through a practical example. We will create a workflow and preset the output to have expected intent and
    entities.

    :param rules: A mapping that defines relationship between an intent, its slots and the entities that fill them.
    :type rules: Rule
    :param fill_multiple: More than one item be allowed to fill a single slot.
    :type fill_multiple: bool
    :param access: Signature for workflow access is :code:`access(workflow) -> (Intent, List[BaseEntity])`
    :type access: Optional[PluginFn]
    :param mutate: Not needed, pass :code:`None`.
    :type mutate: Optional[PluginFn]

    Irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.
    """

    def __init__(
        self,
        rules: Rule,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        fill_multiple: bool = True,
        debug: bool = False,
    ) -> None:
        """
        constructor
        """
        # rules
        #
        # A `Dict` where each key is an intent name, and each value is another `Dict`,
        # in which, each key is an entity and value contains the `slot_name` and `entity_type.`
        #
        # example:
        # ```
        # rules = {"intent": {"slot_name": "entity_type"}}
        # ```
        super().__init__(dest=dest, guards=guards, debug=debug)
        self.rules: Rule = rules or {}

        # fill_multiple
        # A boolean value that commands the slot filler to add multiple values of the
        # same entity type within a slot.
        self.fill_multiple = fill_multiple

    def fill(self, intents: List[Intent], entities: List[BaseEntity]) -> List[Intent]:
        if not intents:
            return intents

        intent, *rest = intents

        intent.apply(self.rules)

        for entity in entities:
            intent.fill_slot(entity, fill_multiple=self.fill_multiple)

        intent.cleanup()
        return [intent, *rest]

    def utility(self, _: Input, output: Output) -> List[Intent]:
        return self.fill(output.intents, output.entities)
