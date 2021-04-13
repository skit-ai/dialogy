"""
.. _intent:
Type definition for `Intent`.

Import classes:

    - Intent
"""

from typing import Any, Callable, Dict, List, Optional

from dialogy.types.entity import BaseEntity
from dialogy.types.plugin import PluginFn
from dialogy.types.slots import Rule, Slot
from dialogy.utils.logger import log


class Intent:
    """
    An instance of this class contains the name of the action associated with a body of text.
    """

    def __init__(
        self,
        name: str,
        score: float,
        parsers: Optional[List[str]] = None,
        alternative_index: Optional[int] = 0,
        slots: Optional[Dict[str, Slot]] = None,
    ) -> None:
        """

        :param name: The name of the intent. A class label
        :type name: str
        :param score: The confidence score from a model.
        :type score: float
        :param parsers: Items that alter the attributes.
        :type parsers: Optional[List[str]]
        :param alternative_index: Out of a list of transcripts, this points at the index which lead to prediction.
        :type alternative_index: Optional[int]
        :param slots: A map of slot names and :ref:`Slot<slot>`
        :type slots: Optional[Dict[str, Slot]]
        """
        # The name of the intent to be used.
        self.name = name

        # The confidence of this intent being present in the utterance.
        self.score = score

        # Trail of functions that modify the attributes of an instance.
        self.parsers = parsers or []

        # In case of an ASR, `alternative_index` points at one of the nth
        # alternatives that help in predictions.
        self.alternative_index = alternative_index

        # Container for holding `List[BaseEntity]`.
        self.slots: Dict[str, Slot] = slots or {}

    def apply(self, rules: Rule) -> "Intent":
        """
        Create slots within the `slots` attribute.

        An intent can hold different entities within associated slot-types.
        """
        rule = rules.get(self.name)
        if not rule:
            return self

        for slot_name, entity_type in rule.items():
            self.slots[slot_name] = Slot(name=slot_name, type_=[entity_type], values=[])
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
        log.debug("Looping through slot_names for each entity.")
        for slot_name in entity.slot_names:
            log.debug("slot_name: %s", slot_name)
            log.debug("intent slots: %s", self.slots)
            if slot_name in self.slots:
                if fill_multiple:
                    self.slots[slot_name].add(entity)
                    return self

                if not self.slots[slot_name].values:
                    log.debug("filling %s into %s", entity, self.name)
                    self.slots[slot_name].add(entity)
                else:
                    log.debug(
                        "removing %s from %s, because the slot was filled previously. "
                        "Use fill_multiple=True if this is not required.",
                        entity,
                        self.name,
                    )
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
        return {
            "name": self.name,
            "score": self.score,
            "alternative_index": self.alternative_index,
            "slots": {slot_name: slot.json() for slot_name, slot in self.slots.items()},
            "parsers": self.parsers,
        }


"""
[Tutorial](../../../tests/types/intents/test_intents.html)
"""
