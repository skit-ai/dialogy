from typing import Any, List, Dict

from loguru import logger

from dialogy.base import Plugin, Input, Output
from dialogy.types import Intent, BaseEntity
from dialogy.types.intent.swap_rules import SwapRule


class RuleBasedIntentSwap(Plugin):
    def __init__(self, rules: List[SwapRule], dest=None, **kwargs) -> None:
        super().__init__(dest=dest, **kwargs)
        self.rules = [SwapRule(**r) for r in rules]

    def make_payload(
        self,
        intents: List[Intent],
        current_state: str,
        entities: List[BaseEntity],
        previous_intent: str) -> Any:
        """
        Make payload in the acceptable format for swap function for this class.
        """
        return {
            'intent': intents[0].name,
            'state': current_state,
            'entity_types': [entity.entity_type for entity in entities],
            'previous_intent': previous_intent
        }

    def swap(self, payload: Dict[str, Any], intents: List[Intent]):
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
