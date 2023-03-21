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
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        rules: Optional[Dict[str, List[Any]]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(guards=guards, dest=dest, **kwargs)

        if rules:
            self.rules = rules[
                "swap_rules"
            ]  # Rules is a python object parsed by yaml and loaded in memory
        else:
            raise ValueError("Rules have not been instantiated")

    def check_present_absent_other_primitives(
        self,
        primitive: str,
        primitive_in: Optional[List[str]],
        primitive_not_in: Optional[List[str]],
    ) -> bool:

        if primitive and primitive_in:
            return primitive in primitive_in
        elif primitive and primitive_not_in:
            return primitive not in primitive_not_in
        return False

    def check_present_absent_transcript(
        self,
        transcripts: Optional[Iterable[str]],
        primitive_in: Optional[List[str]],
        primitive_not_in: Optional[List[str]],
    ) -> bool:

        if transcripts:
            alternatives = "".join(transcripts)
        else:
            raise ValueError("No transcripts provided")

        if (
            alternatives
            and primitive_in
            and any(word in alternatives for word in primitive_in)
        ):
            return True

        elif (
            alternatives
            and primitive_not_in
            and not any(word in alternatives for word in primitive_not_in)
        ):
            return True

        return False

    def calculate_passed_functional_conditions(
        self,
        transcripts: List[str],
        conditions: Dict[str, bool],
    ) -> int:

        total_passed_conditions = 0
        for key, val in conditions.items():
            if transcript_functions_map[key](transcripts) == val:
                total_passed_conditions += 1
        return total_passed_conditions

    def check_present_absent_entity(
        self,
        primitive_ent: List[str],
        primitive_in: Optional[Iterable[str]],
        primitive_not_in: Optional[Iterable[str]],
    ) -> bool:

        if primitive_ent and primitive_in:
            return len(set(primitive_ent) & set(primitive_in)) > 0

        elif primitive_ent and primitive_not_in:
            return len(set(primitive_ent) & set(primitive_not_in)) == 0

        return False

    def calculate_number_of_passed_conditions(
        self,
        type_of_condition: str,
        primitive_conditions: Dict[str, List[str]],
        transcripts: List[str],
        unpacked_entities: Dict[str, Any],
        map_primitive_to_vals: Dict[str, Any],
    ) -> int:

        if type_of_condition not in ["in", "not_in"]:
            raise ValueError(f"{type_of_condition} type of condition does not exist")

        total_passed_conditions = 0
        for primitive, val in primitive_conditions.items():

            if primitive in ["dim", "value", "type", "entity_type"]:

                if self.check_present_absent_entity(
                    primitive_ent=unpacked_entities[primitive],
                    primitive_in=(val if type_of_condition == "in" else None),
                    primitive_not_in=(val if type_of_condition == "not_in" else None),
                ):
                    total_passed_conditions += 1

            elif primitive == "transcript":
                if self.check_present_absent_transcript(
                    transcripts=transcripts,
                    primitive_in=val if type_of_condition == "in" else None,
                    primitive_not_in=val if type_of_condition == "not_in" else None,
                ):
                    total_passed_conditions += 1

            else:
                if self.check_present_absent_other_primitives(
                    primitive=map_primitive_to_vals[primitive],
                    primitive_in=val if type_of_condition == "in" else None,
                    primitive_not_in=val if type_of_condition == "not_in" else None,
                ):
                    total_passed_conditions += 1

        return total_passed_conditions

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
            # Collect all the non_empty ins and or not_ins
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

            # And with all the in_conditions
            passed_in_conditions = self.calculate_number_of_passed_conditions(
                "in",
                primitive_in_conditions,
                transcripts,
                unpacked_entities,
                map_primitive_to_vals,
            )

            passed_not_in_conditions = self.calculate_number_of_passed_conditions(
                "not_in",
                primitive_not_in_conditions,
                transcripts,
                unpacked_entities,
                map_primitive_to_vals,
            )

            total_available_in_conditions = len(primitive_in_conditions)
            total_available_not_in_conditions = len(primitive_not_in_conditions)

            total_functional_conditions = len(transcript_functional_conditions)

            passed_functional_conditions = self.calculate_passed_functional_conditions(
                transcripts, transcript_functional_conditions
            )

            if (
                passed_in_conditions == total_available_in_conditions
                and passed_not_in_conditions == total_available_not_in_conditions
                and total_functional_conditions == passed_functional_conditions
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

        # return intents if rules[0]["mutate"] == "intent" else entities

    # The below static methods are helper methods coming from ashley's StateToIntent code wherein we need to count the number of digits and check if a number is present in more than 50% of transcripts

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
