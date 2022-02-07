"""
.. _intent:
Type definition for `Intent`.

Import classes:

    - Intent
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import attr

from dialogy.types.entity import BaseEntity
from dialogy.types.slots import Rule, Slot
from dialogy.utils.logger import logger


@attr.s
class Intent:
    """
    An instance of this class contains the name of the action associated with a body of text.
    """

    # The name of the intent to be used.
    name: str = attr.ib(kw_only=True, order=False)

    # The confidence of this intent being present in the utterance.
    score: float = attr.ib(kw_only=True, default=0.0, order=True)

    # In case of an ASR, `alternative_index` points at one of the nth
    # alternatives that help in predictions.
    alternative_index: Optional[int] = attr.ib(kw_only=True, default=None, order=False)

    # Trail of functions that modify the attributes of an instance.
    parsers: List[str] = attr.ib(kw_only=True, factory=list, order=False, repr=False)

    # Container for holding `List[BaseEntity]`.
    slots: Dict[str, Slot] = attr.ib(
        kw_only=True, factory=dict, order=False, repr=False
    )

    def apply(self, rules: Rule) -> Intent:
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

    def add_parser(self, plugin: Any) -> Intent:
        """
        Update parsers with the plugin name

        This is to identify the progression in which the plugins were applied to an intent.
        This only helps in debugging and has no production utility.

        :param plugin: The class that modifies this instance. Preferably should be a plugin.
        :type plugin: Plugin
        :return: Calling instance with modifications to :code:`parsers` attribute.
        :rtype: Intent
        """
        plugin_name = plugin if isinstance(plugin, str) else plugin.__class__.__name__
        self.parsers.append(plugin_name)
        return self

    def fill_slot(self, entity: BaseEntity, fill_multiple: bool = False) -> Intent:
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
        logger.debug("Looping through slot_names for each entity.")
        logger.debug(f"intent slots: {self.slots}")
        for slot_name, slot in self.slots.items():
            logger.debug(f"slot_name: {slot_name}")
            logger.debug(
                f"slot type: {slot.types}",
            )
            logger.debug(
                f"entity type: {entity.entity_type}",
            )
            if entity.entity_type in slot.types:
                if fill_multiple:
                    logger.debug(f"filling {entity} into {self.name}.")
                    self.slots[slot_name].add(entity)
                    return self

                if not self.slots[slot_name].values:
                    logger.debug(f"filling {entity} into {self.name}.")
                    self.slots[slot_name].add(entity)
                else:
                    logger.debug(
                        f"removing {entity} from {self.name}, because the slot was filled previously. "
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
            "alternative_index": self.alternative_index,
            "score": self.score,
            "parsers": self.parsers,
            "slots": {slot_name: slot.json() for slot_name, slot in self.slots.items()},
        }
