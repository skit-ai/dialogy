"""
    IntentEntityMutatorPlugin
"""

from typing import Any, List, Optional, Dict, Union, Tuple

from dialogy.base import Input, Output, Plugin, Guard
from dialogy.types import BaseEntity, Intent
from dialogy.plugins.text.intent_entity_mutator.registry import transcript_functions_map

from . import const


class IntentEntityMutatorPlugin(Plugin):
    def __init__(
        self,
        rules: Dict[str, List[Dict[str, Any]]],
        guards: Optional[List[Guard]] = None,
        dynamic_output_path: bool = True,
        replace_output: bool = True,
        **kwargs: Any,
    ) -> None:

        super().__init__(
            guards=guards, dynamic_output_path=dynamic_output_path, replace_output=replace_output, **kwargs
        )

        self.validate_rules(rules)
        self.rules = rules

    def validate_rules(self, rules: Dict[str, List[Dict[str, Any]]]) -> None:

        rules_base_keys = list(rules.keys())

        if not rules_base_keys:
            raise ValueError(
                f"Rules passed are invalid. Did not receive any base key - Possible base keys - [{const.BASE_KEY}]"
            )

        if const.BASE_KEY not in rules_base_keys:
            raise ValueError(
                f"Did not receive {const.BASE_KEY} as the base key, received {rules_base_keys}"
            )

        rules_ = rules[const.BASE_KEY]

        permissible_transcript_functional_condition_keys = list(
            transcript_functions_map.keys()
        )

        for rule in rules_:
            rule_keys = sorted(list(rule.keys()))
            if rule_keys != const.MANDATORY_RULE_KEYS:
                raise ValueError(
                    f"The rule is either missing some keyword or incorrect keyword entered. \
                        Received: {rule_keys}. Expected: {const.MANDATORY_RULE_KEYS}\n"
                    "{rule}"
                )

            mutate = rule[const.MUTATE]
            if mutate not in [const.INTENT, const.ENTITY]:
                raise ValueError(
                    f"The mutate keyword received incorrect value. \
                        Received {mutate}. Expected: intent or entity\n"
                    "{rule}"
                )

            conditions = rule[const.CONDITIONS]

            for primitive, search_lists in conditions.items():
                if primitive not in const.BASE_CONDITION_PRIMITIVES:
                    raise ValueError(
                        f"Received invalid primitive in the rules. Received: {primitive}.  \
                            Expected from: {const.BASE_ENTITY_PRIMITIVES}\n"
                        "{rule}"
                    )

                if search_lists:

                    if primitive == const.ENTITY:
                        received_entity_primitives = list(
                            search_lists.keys()
                        )  # Get keys such as [dim, type, ..]
                        for ent_primitives in received_entity_primitives:
                            if ent_primitives not in const.BASE_ENTITY_PRIMITIVES:
                                raise ValueError(
                                    f"The rule did not receive correct entity sub_type. Received: {ent_primitives} \
                                        Expected: {const.BASE_ENTITY_PRIMITIVES}\n"
                                    "{rule}"
                                )

                    else:
                        received_primitive_keys = list(
                            search_lists.keys()
                        )  # list of dictionaries. [{in: [], not_in: [], }]
                        for key in received_primitive_keys:
                            if isinstance(search_lists[key], list):
                                if key not in const.SUB_PRIMITIVES:
                                    raise ValueError(
                                        f"The rule did not receive the correct list type. Received: {key} \
                                            Expected: {const.SUB_PRIMITIVES}\n"
                                        "{rule}"
                                    )

                            else:  # boolean instance -> Transcript cases
                                if (
                                    primitive == const.TRANSCRIPT
                                    and key
                                    not in permissible_transcript_functional_condition_keys
                                ):
                                    raise ValueError(
                                        f"The function called for transcripts is not registered. \
                                        Function called: {key} \ Permissible Functions: {permissible_transcript_functional_condition_keys}\n"
                                        "{rule}"
                                    )

                                elif primitive != const.TRANSCRIPT:
                                    raise ValueError(
                                        f"The function calls are only applicable for the transcript primitive but registered under {primitive}\n"
                                        "{rule}"
                                    )

    def check_present_absent_primitive_val(
        self,
        primitive_val: Union[str, List[str]],
        check_presence: bool,
        search_list: List[str],
        received_transcripts: bool = False,
    ) -> bool:

        if not received_transcripts:
            if isinstance(primitive_val, str):
                return (
                    primitive_val in search_list
                    if check_presence
                    else primitive_val not in search_list
                )
            elif isinstance(
                primitive_val, list
            ):  # Check for the presence and absence of entities
                return (
                    len(set(primitive_val) & set(search_list)) > 0
                    if check_presence
                    else len(set(primitive_val) & set(search_list)) == 0
                )

        else:  # Check for the presence and absence of certain words in transcripts
            return (
                any(word in primitive_val for word in search_list)
                if check_presence
                else not any(word in primitive_val for word in search_list)
            )

    def check_passed_functional_conditions(
        self,
        transcripts: List[str],
        conditions: Dict[str, bool],
    ) -> bool:

        passed_conditions = True
        for key, val in conditions.items():
            if transcript_functions_map[key](transcripts) != val:
                passed_conditions = False
                break

        return passed_conditions

    def check_passed_conditions(
        self,
        check_presence: bool,
        primitive_conditions: Dict[str, List[str]],
        unpacked_entities: Dict[str, Any],
        map_primitive_to_vals: Dict[str, Any],
    ) -> bool:

        passed_conditions = True
        for primitive, search_list in primitive_conditions.items():

            if not self.check_present_absent_primitive_val(
                primitive_val=map_primitive_to_vals[primitive]
                if primitive
                not in [const.DIM, const.TYPE, const.ENTITY_TYPE, const.VALUE]
                else unpacked_entities[primitive],
                check_presence=check_presence,
                search_list=search_list,
                received_transcripts=True if primitive == const.TRANSCRIPT else False,
            ):
                passed_conditions = False
                break

        return passed_conditions

    def get_transcript_functional_conditions_map(
        self, search_list: Dict[str, Any]
    ) -> Dict[str, bool]:
        return {
            key: value for key, value in search_list.items() if isinstance(value, bool)
        }

    def mutate(
        self,
        current_state: Optional[str],
        previous_intent: Optional[str],
        entities: List[BaseEntity],
        intents: List[Intent],
        transcripts: List[str],
        rules: List[Dict[str, Any]],
    ) -> Tuple[Union[List[Intent], List[BaseEntity]], str]:

        unpacked_entities = {
            const.TYPE: [x.type for x in entities],
            const.DIM: [x.dim for x in entities],
            const.ENTITY_TYPE: [x.entity_type for x in entities],
            const.VALUE: [x.value for x in entities],
        }

        map_primitive_to_vals = {
            const.INTENT: intents[0].name,
            const.STATE: current_state,
            const.TRANSCRIPT: " ".join(transcripts),
            const.PREVIOUS_INTENT: previous_intent,
        }
        for rule in rules:

            conditions = rule[const.CONDITIONS]

            mutate_to = rule[const.MUTATE_TO]

            primitive_in_conditions = {}
            primitive_not_in_conditions = {}
            transcript_functional_conditions = {}

            for primitive, primitive_search_lists in conditions.items():

                if primitive_search_lists:
                    if primitive == const.TRANSCRIPT:
                        transcript_functional_conditions = (
                            self.get_transcript_functional_conditions_map(
                                primitive_search_lists
                            )
                        )

                    elif primitive == const.ENTITY:
                        for (
                            entity_primitive,
                            entity_values,
                        ) in primitive_search_lists.items():
                            if entity_values.get(const.IN):
                                primitive_in_conditions[
                                    entity_primitive
                                ] = entity_values.get(const.IN)

                            if entity_values.get(const.NOT_IN):
                                primitive_not_in_conditions[
                                    entity_primitive
                                ] = entity_values.get(const.NOT_IN)
                    else:
                        if primitive_search_lists.get(const.IN):
                            primitive_in_conditions[
                                primitive
                            ] = primitive_search_lists.get(const.IN)

                        if primitive_search_lists.get(const.NOT_IN):
                            primitive_not_in_conditions[
                                primitive
                            ] = primitive_search_lists.get(const.NOT_IN)

            passed_in_conditions = self.check_passed_conditions(
                True,
                primitive_in_conditions,
                unpacked_entities,
                map_primitive_to_vals,
            )

            passed_not_in_conditions = self.check_passed_conditions(
                False,
                primitive_not_in_conditions,
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
                if rule[const.MUTATE] == const.INTENT:
                    intents[0].name = mutate_to
                    return intents, const.OUTPUT_DEST_INTENT
                else:
                    mutate_entities = entities
                    if mutate_to:
                        mutate_entities.append(BaseEntity.from_dict(mutate_to))
                    else:
                        mutate_entities = []
                    return mutate_entities, const.OUTPUT_DEST_ENTITY

        return intents, const.OUTPUT_DEST_INTENT

    async def utility(
        self, input_: Input, output: Output
    ) -> Tuple[Union[List[Intent], List[BaseEntity]], str]:

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
            rules=self.rules[const.BASE_KEY],
        )
