from typing import Any, Dict, List, Optional, Union

import yaml

from dialogy.base import Guard, Input, Output, Plugin
from dialogy.plugins.text.intent_entity_mutator.actions_on_primitives import (
    get_len_of_digits,
    is_number_absent,
)
from dialogy.types import BaseEntity, Intent


transcript_functions_map = {
    "is_number_absent": is_number_absent,
    "get_len_of_digits": get_len_of_digits,
}


def check_present_absent(
    primitive: str, present_in: List[str], present_not_in: List[str]
) -> bool:
    if present_in:
        return primitive in present_in
    else:
        return primitive not in present_not_in


def check_present_absent_transcript(
    conditions: Dict[str, Any],
):
    function_conditions = []
    for key, val in conditions:
        if isinstance(val, bool) and val:
            function_conditions.append(key)
    
    val_in = conditions.get('in')
    val_not_in = conditions.get('not_in')

    pass


def check_present_absent_entity(
    primitive_ent: List[str],
    present_in: Optional[List[str]] = None,
    present_not_in: Optional[List[str]] = None,
) -> bool:

    if present_in:
        total_len = len(set(primitive_ent) & set(present_in))
        return total_len > 0

    else:
        return len(set(primitive_ent) & set(present_not_in)) == 0


def mutate_intent(
    current_state: Optional[str],
    previous_intent: Optional[str],
    entities: List[BaseEntity],
    intents: List[Intent],
    transcripts: List[str],
    rules,
) -> List[Intent]:

    unpacked_entities = {
        "type": [x.type for x in entities],
        "dim": [x.dim for x in entities],
        "entity_type": [x.entity_type for x in entities],
        "value": [x.value for x in entities],
    }
    rules = rules["swap_rules"]

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

        for primitive, vals in conditions.items():
            if vals:
                if vals.get("in"):
                    primitive_in_conditions[primitive] = vals.get("in")

                if vals.get("not_in"):
                    primitive_not_in_conditions[primitive] = vals.get("not_in")

            if primitive == "entity" and vals:
                enitity_conditions = vals
                for entity_primitive, entity_vals in enitity_conditions.items():
                    if entity_vals.get("in"):
                        primitive_in_conditions[entity_primitive] = entity_vals.get(
                            "in"
                        )

                    if entity_vals.get("not_in"):
                        primitive_not_in_conditions[entity_primitive] = entity_vals.get(
                            "not_in"
                        )

        # And with all the in_conditions

        total_in_conditions = 0
        for primitive, val_in in primitive_in_conditions.items():

            if primitive in ["dim", "value", "type", "entity_type"]:
                if check_present_absent_entity(
                    unpacked_entities[primitive], present_in=val_in, present_not_in=None
                ):
                    total_in_conditions += 1

            elif primitive == "transcript":

                if check_present_absent_transcript():
                    total_in_conditions += 1

            else:
                if check_present_absent(
                    map_primitive_to_vals.get(primitive),
                    present_in=val_in,
                    present_not_in=None,
                ):
                    total_in_conditions += 1

        total_not_in_conditions = 0
        for primitive, val_not_in in primitive_not_in_conditions.items():

            if primitive in ["dim", "value", "type", "entity_type"]:
                if check_present_absent_entity(
                    unpacked_entities[primitive],
                    present_in=None,
                    present_not_in=val_not_in,
                ):
                    total_not_in_conditions += 1

                elif primitive == "transcript":
                    if check_present_absent_transcript():
                        total_not_in_conditions += (1,)

            else:
                if check_present_absent(
                    map_primitive_to_vals.get(primitive),
                    present_in=None,
                    present_not_in=val_not_in,
                ):
                    total_not_in_conditions += 1

        if total_in_conditions == len(
            primitive_in_conditions
        ) and total_not_in_conditions == len(primitive_not_in_conditions):
            intents[0].name = mutate_to
            return intents

    return intents


def test_func(
    rules,
    name=None,
    current_state=None,
    previous_intent=None,
    transcripts=["change my seat"],
):
    intent = Intent(name=name, score=0.4)
    entity_dict = {
        "type": "random",
        "entity_type": "",
        # this was parser earlier
        "parsers": ["other-reason-parser"],
        # this was values earlier, and structure has also changed (referenced https://gitlab.com/vernacularai/ai/clients/oppo-v1/-/blob/master/slu/src/controller/custom_plugins.py#L539)
        # "value": {
        #     "values": [
        #         {"value": rlabel},
        #     ],
        # },
        "value": "",
        "score": 20,
        # newly added attributes
        "dim": "",
        "latent": True,
        "range": {"start": 0, "end": 0},
        # "start": 0,
        # "end": 0,
        "body": "",
    }
    entities = [BaseEntity.from_dict(entity_dict)]
    intents = [intent]

    intents = mutate_intent(
        current_state,
        previous_intent,
        entities,
        intents,
        transcripts,
        rules,
    )
    print(intents[0].name, "INTENT")


if __name__ == "__main__":
    with open(
        "/home/sanchit/dialogy/tests/plugin/text/intent_entity_mutator/mutate_intent.yaml",
        "r",
    ) as f:
        rules = yaml.load(f, Loader=yaml.Loader)
    test_func(
        rules, "web_check_in_seat_selection_compulsory", "COF", ["change my seat"]
    )
