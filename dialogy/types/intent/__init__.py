"""
.. _intent:
Type definition for `Intent`.

Import classes:

    - Intent
"""

from typing import Any, Dict, List, Optional

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
        Create slots using :ref:`rules`.

        An intent can hold different entities within associated slot-types.

        :param rules: A configuration for slot names and entity types associated with this instance of Intent.
        :type rules: Rule
        :return: The calling Intent is modified to have :ref:`Slots <slot>`.
        :rtype: Intent
        """
        rule = rules.get(self.name)
        if not rule:
            return self

        for slot_name, entity_types in rule.items():
            if isinstance(entity_types, str):
                entity_type = entity_types
                self.slots[slot_name] = Slot(
                    name=slot_name, types=[entity_type], values=[]
                )
            elif isinstance(entity_types, list) and all(
                isinstance(type_, str) for type_ in entity_types
            ):
                self.slots[slot_name] = Slot(
                    name=slot_name, types=entity_types, values=[]
                )
            else:
                raise TypeError(
                    f"Expected entity_types={entity_types} in the rule"
                    f" {rule} to be a List[str] but {type(entity_types)} was found."
                )

        return self

    def add_parser(self, postprocessor: PluginFn) -> "Intent":
        """
        Update parsers with the postprocessor function name

        This helps us identify the progression in which the postprocessing functions
        were applied to an intent. This helps in debugging and has no production utility

        :param postprocessor: The callable that modifies this instance. Preferably should be a plugin.
        :type postprocessor: PluginFn
        :return: Calling instance with modifications to :code:`parsers` attribute.
        :rtype: Intent
        """
        self.parsers.append(postprocessor.__name__)
        return self

    def fill_slot(self, entity: BaseEntity, fill_multiple: bool = False) -> "Intent":
        """
        Update :code:`slots[slot_type].values` with a single entity.

        We will explore the possibility of sharing/understanding the meaning of multiple entities
        in the same slot type.

        There maybe cases where we want to fill multiple entities of the same type within a slot.
        In these cases :code:`fill_multiple` should be set to True.

        The :ref:`RuleBasedSlotFillerPlugin <rule_slot_filler>` has a detailed demo for this.

        :param entity: The entity to be checked for support in the calling intent's slots.
        :type entity: BaseEntity
        :param fill_multiple:
        :type fill_multiple: bool
        :return: The calling Intent with modifications to its slots.
        :rtype: Intent
        """
        log.debug("Looping through slot_names for each entity.")
        log.debug("intent slots: %s", self.slots)
        for slot_name, slot in self.slots.items():
            log.debug("slot_name: %s", slot_name)
            log.debug("slot type: %s", slot.types)
            log.debug("entity type: %s", entity.type)
            if entity.type in slot.types:
                if fill_multiple:
                    self.slots[slot_name].add(entity)
                    return self

                if not self.slots[slot_name].values:
                    log.debug("filling %s into %s.", entity, self.name)
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

        .. ipython:: python

            from dialogy.types.intent import Intent

            intent = Intent(name="special", score=0.8)
            intent.json()
        """
        return {
            "name": self.name,
            "score": self.score,
            "alternative_index": self.alternative_index,
            "slots": {slot_name: slot.json() for slot_name, slot in self.slots.items()},
            "parsers": self.parsers,
        }

    def __repr__(self) -> str:
        return f"Intent(name={self.name}, score={self.score}, slots={self.slots})"
