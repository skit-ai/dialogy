from typing import Any, Dict, List, Union

from loguru import logger

from dialogy.base import Input, Output, Plugin
from dialogy.types import BaseEntity, Intent
from dialogy.types.intent.swap_rules import SwapRule


class RuleBasedIntentSwap(Plugin):
    """
    .. _RuleBasedIntentSwap:

    We require custom logic to handle arbitrary transitions. Giving a detailed look, the transitions
    appear to have simple relationships that can even be serialized and expressed as configs.

    Taking an example:

    If we have discovered in an utterance, that the current state is :code:`S1` and the intent is :code:`I2` and in this case,
    we should transition to :code:`I2`. Then this can be expressed by the following rule:

    .. code-block:: python

        rules = [{
            rename: "I2",
            depends_on: {
                "intent": "I1",
                "state": "S1"
            }
        }]

    We can do more; say we have discovered

    entity types as: :code:`["e1", "e2"]`
    state as :code:`s1`
    and we need to transition to :code:`I2`?

    .. code-block:: python

        rules = [{
        rename: "I2",
            depends_on: {
                "entities": {
                    "intersects": ["e1"]
                },
                "state": "S1"
            }
        }]

    We have also identified that these transitions currently exist for the following properties:

    1. The predicted intent with most confidence.
    2. The current state
    3. The list of entity types
    4. The previous intent
    
    By accommodating 5 operations for each of the 4 properties we can produce a moderately strong rule transition, namely:

    1. eq - equality check, also the default operation
    2. ne - not equal
    3. in - containership
    4. nin - inverse containership
    5. intersects - an intersection between two sets (or array-like) quantities.

    This can help in cases where there is a dire shortage of data. The **source** code of :ref:`swap rules<SwapRulesModule>` could be a helpful read.
    """
    def __init__(self, rules: List[Dict[str, Any]], dest: str = "output.intents", **kwargs: Any) -> None:
        super().__init__(dest=dest, **kwargs)
        self.rules = [SwapRule(**r) for r in rules]

    def make_payload(
        self,
        intents: List[Intent],
        current_state: Union[None, str],
        entities: List[BaseEntity],
        previous_intent: Union[None, str]) -> Any:
        """
        Make payload in the acceptable format for swap function for this class.
        """
        return {
            "intent": intents[0].name,
            "state": current_state,
            "entity_types": [entity.entity_type for entity in entities],
            "entity_values": [entity.get_value() for entity in entities],
            "previous_intent": previous_intent
        }

    def swap(self, payload: Dict[str, Any], intents: List[Intent]) -> List[Intent]:
        """
        Swap intent name based on the rules defined in config.yaml under intent_swap 
        """
        updates = [rule.rename for rule in self.rules if rule.parse(payload)]
        if len(updates) == 1:
            intents[0].name = updates[0]
            intents[0].add_parser(self.__class__.__name__)

        if len(updates) > 1:
            logger.error(f"More than one rule matched for {payload}")

        return intents


    def utility(self, input_: Input, output: Output) -> Any:
        payload = self.make_payload(output.intents, input_.current_state, output.entities, input_.previous_intent)
        return self.swap(payload, output.intents)
