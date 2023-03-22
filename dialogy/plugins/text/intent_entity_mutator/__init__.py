"""
    IntentEntityMutatorPlugin
"""

from typing import Any, List, Optional, Dict, Iterable, Union, Callable

from dialogy.base import Input, Output, Plugin, Guard
from dialogy.types import BaseEntity, Intent

from dialogy.plugins.text.intent_entity_mutator.actions_on_primitives import (
    contain_digits,
    is_number_absent,
)

transcript_functions_map: Dict[str, Callable[[List[str]], int]] = {
    "is_number_absent": is_number_absent,
    "contain_digits": contain_digits,
}


class IntentEntityMutatorPlugin(Plugin):
    def __init__(
        self,
        rules: Dict[str, List[Any]],
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(guards=guards, dest=dest, **kwargs)
        self.rules = rules["swap_rules"]

    def check_present_absent_other_primitives(
        self,
        primitive_val: str,
        check_presence: bool,
        primitive_val_in_not_in: List[str],
    ) -> bool:

        return (
            primitive_val in primitive_val_in_not_in
            if check_presence
            else primitive_val not in primitive_val_in_not_in
        )

    def check_present_absent_transcript(
        self,
        transcripts: Iterable[str],
        check_presence: bool,
        primitive_val_in_not_in: List[str],
    ) -> bool:

        alternatives = "".join(transcripts)

        return (
            any(word in alternatives for word in primitive_val_in_not_in)
            if check_presence
            else not any(word in alternatives for word in primitive_val_in_not_in)
        )

    def check_passed_functional_conditions(
        self,
        transcripts: List[str],
        conditions: Dict[str, bool],
    ) -> bool:

        passed_conditions = True
        for key, val in conditions.items():
            if not transcript_functions_map[key](transcripts) == val:
                passed_conditions = False
                break

        return passed_conditions

    def check_present_absent_entity(
        self,
        primitive_ent_val: List[str],
        check_presence: bool,
        primitive_val_in_not_in: Iterable[str],
    ) -> bool:

        return (
            len(set(primitive_ent_val) & set(primitive_val_in_not_in)) > 0
            if check_presence
            else len(set(primitive_ent_val) & set(primitive_val_in_not_in)) == 0
        )

    def check_passed_conditions(
        self,
        type_of_condition: str,
        primitive_conditions: Dict[str, List[str]],
        transcripts: List[str],
        unpacked_entities: Dict[str, Any],
        map_primitive_to_vals: Dict[str, Any],
    ) -> bool:

        if type_of_condition not in ["in", "not_in"]:
            raise ValueError(f"{type_of_condition} type of condition does not exist")

        passed_conditions = True
        for primitive, val in primitive_conditions.items():

            if primitive in ["dim", "value", "type", "entity_type"]:

                if not self.check_present_absent_entity(
                    primitive_ent_val=unpacked_entities[primitive],
                    check_presence=True if type_of_condition == "in" else False,
                    primitive_val_in_not_in=val,
                ):
                    passed_conditions = False
                    break

            elif primitive == "transcript":
                if not self.check_present_absent_transcript(
                    transcripts=transcripts,
                    check_presence=True if type_of_condition == "in" else False,
                    primitive_val_in_not_in=val,
                ):
                    passed_conditions = False
                    break

            else:
                if not self.check_present_absent_other_primitives(
                    primitive_val=map_primitive_to_vals[primitive],
                    check_presence=True if type_of_condition == "in" else False,
                    primitive_val_in_not_in=val,
                ):
                    passed_conditions = False
                    break

        return passed_conditions

    def mutate(
        self,
        current_state: Optional[str],
        previous_intent: Optional[str],
        entities: List[BaseEntity],
        intents: List[Intent],
        transcripts: List[str],
        rules: List[Dict[str, Any]],
    ) -> Union[List[Intent], List[BaseEntity]]:

        unpacked_entities = {
            "type": [x.type for x in entities],
            "dim": [x.dim for x in entities],
            "entity_type": [x.entity_type for x in entities],
            "value": [x.value for x in entities],
        }

        map_primitive_to_vals = {
            "intent": intents[0].name,
            "state": current_state,
            "transcript": " ".join(transcripts),
            "previous_intent": previous_intent,
        }
        for rule in rules:

            conditions = rule["conditions"]

            mutate_to = rule["mutate_to"]

            primitive_in_conditions = {}
            primitive_not_in_conditions = {}
            transcript_functional_conditions = {}

            for primitive, vals in conditions.items():

                if primitive == "transcript" and vals:
                    transcript_functional_conditions = {
                        key: value
                        for key, value in vals.items()
                        if isinstance(value, bool)
                    }

                if vals:
                    if vals.get("in"):
                        primitive_in_conditions[primitive] = vals.get("in")

                    if vals.get("not_in"):
                        primitive_not_in_conditions[primitive] = vals.get("not_in")

                if primitive == "entity" and vals:
                    for entity_primitive, entity_vals in vals.items():
                        if entity_vals.get("in"):
                            primitive_in_conditions[entity_primitive] = entity_vals.get(
                                "in"
                            )

                        if entity_vals.get("not_in"):
                            primitive_not_in_conditions[
                                entity_primitive
                            ] = entity_vals.get("not_in")

            passed_in_conditions = self.check_passed_conditions(
                "in",
                primitive_in_conditions,
                transcripts,
                unpacked_entities,
                map_primitive_to_vals,
            )

            passed_not_in_conditions = self.check_passed_conditions(
                "not_in",
                primitive_not_in_conditions,
                transcripts,
                unpacked_entities,
                map_primitive_to_vals,
            )

            passed_functional_conditions = self.check_passed_functional_conditions(
                transcripts, transcript_functional_conditions
            )

            if (
                passed_in_conditions
                and passed_not_in_conditions
                and passed_functional_conditions
            ):
                if rule["mutate"] == "intent":
                    intents[0].name = mutate_to
                    return intents
                else:
                    mutate_entities = [BaseEntity.from_dict(mutate_to)]
                    return mutate_entities

        if rules[0]["mutate"] == "intent":
            return intents

        return entities

    def utility(
        self, input_: Input, output: Output
    ) -> Union[List[Intent], List[BaseEntity]]:

        current_state = input_.current_state
        intents = output.intents
        entities = output.entities
        previous_intent = input_.previous_intent
        transcripts = input_.transcripts

        return self.mutate(
            current_state=current_state,
            previous_intent=previous_intent,
            entities=entities,
            intents=intents,
            transcripts=transcripts,
            rules=self.rules,
        )
