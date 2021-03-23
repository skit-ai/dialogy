"""
Type definition for `Intent`.

Import classes:

    - Intent
"""

from typing import Any, Callable, Dict, List, Optional

import attr

from dialogy.types.entity import BaseEntity
from dialogy.types.plugin import PluginFn
from dialogy.types.slots import Rule, Slot


@attr.s
class Intent:
    """
    An instance of this class contains the name of the action associated with a body of text.
    """

    # The name of the intent to be used.
    name = attr.ib(type=str)

    # The confidence of this intent being present in the utterance.
    score = attr.ib(type=float)

    # Trail of functions that modify the attributes of an instance.
    parsers = attr.ib(type=List[str], default=attr.Factory(list))

    # In case of an ASR, `alternative_index` points at one of the nth
    # alternatives that help in predictions.
    alternative_index = attr.ib(type=Optional[int], default=0)

    # Container for holding `List[BaseEntity]`.
    slots = attr.ib(type=Dict[str, Slot], default=attr.Factory(dict))

    def apply(self, rules: Rule) -> "Intent":
        """
        Create slots within the `slots` attribute.

        An intent can hold different entities within associated slot-types.
        """
        rule = rules.get(self.name)
        if not rule:
            return self

        for slot_name, entity_type in rule.items():
            self.slots[slot_name] = Slot(name=slot_name, type=[entity_type], values=[])
        return self

    def add_parser(self, postprocessor: PluginFn) -> "Intent":
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an intent. This helps in debugging and has no production utility
        """
        self.parsers.append(postprocessor.__name__)
        return self

    def fill_slot(self, entity: BaseEntity, fill_multiple: bool = False) -> "Intent":
        """
        Update `slots[slot_type].values` with a single entity.

        We will explore the possibility of sharing/understanding the meaning of multiple entities
        in the same slot type.

        There maybe cases where we want to fill multiple entities of the same type within a slot.
        In these cases fill_multiple should be set to True.

        Args:
            entity (BaseEntity): [entities](../../docs/entity/__init__.html)
        """
        for slot_name in entity.slot_names:
            if slot_name in self.slots:
                if fill_multiple:
                    self.slots[slot_name].add(entity)
                    return self

                if not self.slots[slot_name].values:
                    self.slots[slot_name].add(entity)
                else:
                    self.slots[slot_name].clear()
        return self

    def cleanup(self) -> None:
        """
        Remove slots that were not filled.
        """
        slot_names = list(self.slots.keys())
        for slot_name in slot_names:
            if not self.slots[slot_name].values:
                del self.slots[slot_name]

    def json(self) -> Dict[str, Any]:
        """
        Convert the object to a dictionary.
        """
        intent = self
        intent_slots = {}
        for slot_name in intent.slots:
            intent_slots[slot_name] = intent.slots[slot_name].json()

        intent_json = attr.asdict(self)
        intent_json["slots"] = intent_slots
        return intent_json


"""
[Tutorial](../../../tests/types/intents/test_intents.html)
"""
