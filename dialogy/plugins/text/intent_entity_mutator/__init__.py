"""
    IntentEntityMutatorPlugin
"""

from typing import Any, Callable, Dict, List, Optional, Union

from dialogy.base.plugin import Input, Output, Plugin
from dialogy.types import BaseEntity, Intent
from dialogy.workflow import Workflow


class IntentEntityMutatorPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        guards=None,
        rules=None,
        **kwargs,
    ):
        super().__init__(dest=dest, **kwargs)
        if rules:
            self.rules = rules[
                "swap_rules"
            ]  # Rules is a python object parsed by yaml and loaded in memory

    def mutate_intent(
        self,
        current_state: str = None,
        previous_intent: str = None,
        entities: List[BaseEntity] = None,
        intents: List[Intent] = None,
        transcripts: List[str] = None,
    ) -> List[Intent]:

        for rule in self.rules:
            conditions = rule[
                "conditions"
            ]  # This is the list of all the conditions in the rules

            # The below code mostly covers `ContextualIntentSwap` and `RuleBasedIntentSwap` patterns

            mutate_to = rule["mutate_to"]

            if conditions["intent"]:
                intent_in = conditions["intent"]["in"]
                intent_not_in = conditions["intent"]["not_in"]

            if conditions["state"]:
                state_in = conditions["state"]["in"]

            if conditions["previous_intent"]:
                previous_intent_in = conditions["previous_intent"]["in"]

            if conditions["transcript"]:
                transcript_in = conditions["transcript"]["in"]

            # Entity sub_types
            entity = conditions["entity"]
            if entity:
                entity_type_in = conditions["entity"]["type"]["in"]

                entity_value_in = conditions["entity"]["value"]["in"]

                entity_dim_in = conditions["entity"]["dim"]["in"]

            if intents[0].name in intent_in:
                print("WORK")

                if current_state and (current_state in state_in):
                    if entity:
                        mutated_intent = self.handle_entity_cases(
                            entities,
                            intents,
                            mutate_to,
                            entity_type_in,
                            entity_value_in,
                            entity_dim_in,
                        )
                        if mutated_intent[0].name == intents[0].name:
                            continue
                        else:
                            return intents

                    elif conditions["transcript"] and conditions["transcript"]["in"]:
                        transcript_in = conditions["transcript"]["in"]
                        alternatives = "".join(transcripts)
                        if intents[0].name in intent_in and (
                            any(word in alternatives for word in transcript_in)
                        ):
                            intents[0].name = mutate_to
                            return intents

                    else:
                        intents[0].name = mutate_to
                        return intents

                elif entity:
                    mutated_intent = self.handle_entity_cases(
                        entities,
                        intents,
                        mutate_to,
                        entity_type_in,
                        entity_value_in,
                        entity_dim_in,
                    )
                    if mutated_intent[0].name == intents[0].name:
                        continue
                    else:
                        return intents

            elif current_state and (current_state in state_in):
                if entity:
                    mutated_intent = self.handle_entity_cases(
                        entities,
                        intents,
                        mutate_to,
                        entity_type_in,
                        entity_value_in,
                        entity_dim_in,
                    )
                    if mutated_intent[0].name == intents[0].name:
                        continue
                    else:
                        return intents

                elif previous_intent and (previous_intent in previous_intent_in):
                    if entity:
                        mutated_intent = self.handle_entity_cases(
                            entities,
                            intents,
                            mutate_to,
                            entity_type_in,
                            entity_value_in,
                            entity_dim_in,
                        )

                        if mutated_intent[0].name == intents[0].name:
                            continue
                        else:
                            return intents

                    else:
                        intents[0].name = mutate_to
                        return intents

                elif transcripts:
                    if self.is_number_absent(transcripts):
                        if intents[0].name not in intent_not_in:
                            intents[0].name = mutate_to
                            return intents

                    else:
                        is_not_callback = not (
                            intents[0].name == "_callback_"
                            and self.get_len_of_digits(transcripts) < 5
                        )
                        if is_not_callback:
                            intents[0].name = mutate_to
                            return intents
                        else:
                            return intents

                else:
                    intents[0].name = mutate_to
                    return intents
            else:
                continue

                # Callback specific case from `StateToIntent`

        return intents

    def mutate_entity(
        self,
        intents: List[Intent],
        current_state: str,
        entities: List[BaseEntity],
    ) -> List[BaseEntity]:
        pass

    def mutate_original_intent(
        self,
        current_intents: List[Intent],
    ):
        pass

    @staticmethod
    def handle_entity_cases(
        entities: List[BaseEntity],
        intents: List[Intent],
        mutate_to: str,
        entity_type_in: Union[List[str], None],
        entity_value_in: Union[List[str], None],
        entity_dim_in: Union[List[str], None],
    ) -> List[Intent]:

        if entity_type_in and entity_value_in:
            for ent_type_in in entity_type_in:
                for ent_value_in in entity_value_in:
                    if ent_type_in in [x.type for x in entities]:
                        if ent_value_in in [x.value for x in entities]:
                            intents[0].name = mutate_to
                            return intents
                        else:
                            return intents

        if entity_dim_in:
            for ent_dim_in in entity_dim_in:
                if ent_dim_in in [x.dim for x in entities]:
                    intents[0].name = mutate_to
                    return intents

        if entity_type_in:
            for ent_type_in in entity_type_in:
                if ent_type_in in [x.type for x in entities]:
                    intents[0].name = mutate_to
                    return intents

        else:
            return intents

        return intents

    # The below static methods are helper methods coming from ashley's StateToIntent code wherein we need to count the number of digits and check if a number is present in more than 50% of transcripts

    @staticmethod
    def is_number_absent(transcripts: List[str]) -> bool:
        num_transcripts_with_digits = 0
        for word in transcripts:
            if any(char.isdigit() for char in word):
                num_transcripts_with_digits += 1
        if (
            num_transcripts_with_digits / len(transcripts)
        ) > 0.5:  # consider it as a number only if a number is present in more than 50% of the transcripts
            return False
        return True

    @staticmethod
    def get_len_of_digits(ner_input: List[str]) -> bool:
        first_alternative = ner_input[0]
        return sum(c.isdigit() for c in first_alternative)

    def utility(self, input_: Input, output: Output) -> Any:

        current_state = input_.current_state
        intents = output.intents
        entities = output.entities
        previous_intent = input_.previous_intent
        transcripts = input_.transcripts

        if self.rules[0]["mutate"] == "intent":
            return self.mutate_intent(
                current_state, previous_intent, entities, intents, transcripts
            )

        elif self.rules[0]["mutate"] == "entity":
            return self.mutate_entity(
                current_state, previous_intent, current_state, entities
            )

        else:
            return self.mutate_original_intent(intents)


def test_intent_entity_plugin(name, rules, current_state, previous_intent):
    entity_dict = {
        "type": "next_bill_cycle",
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
    entity = BaseEntity.from_dict(entity_dict)
    intent_entity = IntentEntityMutatorPlugin(rules=rules)
    workflow = Workflow([intent_entity])
    intent = Intent(name=name, score=0.4)

    body = [[{"transcript": ""}]]
    inp = Input(
        utterances=body, current_state=current_state, previous_intent=previous_intent
    )
    out = Output(intents=[intent], entities=[entity])
    # print(out,"CHECK")
    _, out = workflow.run(inp, out)
    print(out.intents[0].name, "INTENT")


entity_dict = {
    "type": "",
    "entity_type": "",
    # this was parser earlier
    "parsers": ["other-reason-parser"],
    # this was values earlier, and structure has also changed (referenced https://gitlab.com/vernacularai/ai/clients/oppo-v1/-/blob/master/slu/src/controller/custom_plugins.py#L539)
    # "value": {
    #     "values": [
    #         {"value": rlabel},
    #     ],
    # },
    "value": "whatsapp",
    "score": "",
    # newly added attributes
    "dim": "extra_baggage_intent",
    "latent": True,
    "range": {"start": 0, "end": 0},
    # "start": 0,
    # "end": 0,
    "body": "",
}
