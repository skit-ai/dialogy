"""
.. _rule_slot_filler:

Module provides access to a rule-based :ref:`slot filler<slot_filler>`.
"""
from typing import Any, List, Optional

from dialogy.base.plugin import Plugin
from dialogy.types.entity import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.types.slots import Rule
from dialogy.utils.logger import dbg, log


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

    .. ipython:: python

        import yaml
        from pprint import pprint
        from dialogy.workflow import Workflow
        from dialogy.plugins import RuleBasedSlotFillerPlugin
        from dialogy.types.intent import Intent
        from dialogy.types.entity import PeopleEntity, NumericalEntity

        # ---------------------------------------------------------------------------------------------------
        # Create rules
        rule_string = \"""
        faqs:
            number_slot: number
        count_people:
            number_slot:
            - people
            - number
        \"""
        slot_rules = yaml.safe_load(rule_string)
        # ---------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------
        # Setting up the plugin
        slot_filler = RuleBasedSlotFillerPlugin(rules=slot_rules, access=lambda w: w.output, debug=True)()
        # ---------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------
        # Creating synthetic values.
        # normally you'd get these by running the workflow with models.
        intent = Intent(name="count_people", score=1)
        number_entity = NumericalEntity(type="number", range={"start": 0, "end": 7}, body='2 people', latent=False, values=[{"values":2}], dim="number")
        people_entity = PeopleEntity(type="people", range={"start": 0, "end": 7}, body='2 people', latent=False, values=[{"values":2}], dim="people")
        entities = [people_entity, number_entity]
        # ---------------------------------------------------------------------------------------------------

        # ---------------------------------------------------------------------------------------------------
        # setting up the workflow to use slot_filler
        workflow = Workflow(preprocessors=[], postprocessors=[slot_filler], debug=True)
        # ---------------------------------------------------------------------------------------------------

        # If you notice the instantiation of RuleBasedSlotFillerPlugin,
        # you will notice the `access` method expects a Tuple of two elements.
        workflow.output = (intent, entities)

        workflow.run(input_="2 am")



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
        fill_multiple: bool = False,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
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
        super().__init__(access=access, mutate=mutate, debug=debug)
        self.rules: Rule = rules or {}

        # fill_multiple
        # A boolean value that commands the slot filler to add multiple values of the
        # same entity type within a slot.
        self.fill_multiple = fill_multiple

    def fill(self, intent: Intent, entities: List[BaseEntity]) -> None:
        intent.apply(self.rules)

        for entity in entities:
            intent.fill_slot(entity, fill_multiple=self.fill_multiple)

        intent.cleanup()
        log.debug("intent after slot-filling: %s", intent)

    @dbg(log)
    def utility(self, *args: Any) -> Any:
        return self.fill(*args)  # pylint: disable=no-value-for-parameter
