"""
    IntentEntityMutatorPlugin
"""

from typing import Any, List, Union

from dialogy.base.plugin import Input, Output, Plugin
from dialogy.types import BaseEntity, Intent
import copy
from dialogy.workflow import Workflow
from dialogy.plugins.text.intent_entity_mutator.actions_on_primitives import (
    custom_logic_on_transcripts,
)


class IntentEntityMutatorPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        guards=None,
        rules=None,
        **kwargs,
    ):
        super().__init__(guards=guards, dest=dest, **kwargs)
        if rules:
            self.rules = rules[
                "swap_rules"
            ]  # Rules is a python object parsed by yaml and loaded in memory
        else:
            raise TypeError("Rules have not been instantiated")

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

            # Entity sub_types
            entity_in = conditions["entity"]
            if entity_in:
                entity_type_in = conditions["entity"]["type"]["in"]

                entity_entitytype_in = conditions["entity"]["entity_type"]["in"]

                entity_value_in = conditions["entity"]["value"]["in"]

                entity_dim_in = conditions["entity"]["dim"]["in"]

            if intents[0].name in intent_in:
                if state_in and (current_state in state_in):
                    if entity_in:
                        mutated_intent = self.handle_entity_cases(
                            entities,
                            intents,
                            mutate_to,
                            entity_entitytype_in,
                            entity_type_in,
                            entity_value_in,
                            entity_dim_in,
                        )
                        if mutated_intent[0].name == intents[0].name:
                            continue
                        else:
                            intents[0].name = mutated_intent[0].name
                            return intents

                    elif conditions["transcript"] and conditions["transcript"]["in"]:
                        transcript_in = conditions["transcript"]["in"]
                        alternatives = "".join(transcripts)
                        if any(word in alternatives for word in transcript_in):
                            intents[0].name = mutate_to
                            return intents

                    elif conditions["previous_intent"]:
                        if previous_intent in previous_intent_in:
                            intents[0].name = mutate_to

                    else:
                        intents[0].name = mutate_to
                        return intents

                elif not state_in and entity_in:
                    mutated_intent = self.handle_entity_cases(
                        entities,
                        intents,
                        mutate_to,
                        entity_entitytype_in,
                        entity_type_in,
                        entity_value_in,
                        entity_dim_in,
                    )
                    if mutated_intent[0].name == intents[0].name:
                        continue
                    else:
                        intents[0].name = mutated_intent[0].name
                        return intents

            elif state_in and (current_state in state_in):

                if entities and entity_in:
                    mutated_intent = self.handle_entity_cases(
                        entities,
                        intents,
                        mutate_to,
                        entity_entitytype_in,
                        entity_type_in,
                        entity_value_in,
                        entity_dim_in,
                    )
                    if mutated_intent[0].name == intents[0].name:
                        continue
                    else:
                        intents[0].name = mutated_intent[0].name
                        return intents

                elif (
                    transcripts
                    and conditions["transcript"]
                    and conditions["transcript"]["transcript_apply_func"]
                ):
                    # Ashley had this custom check
                    mutated_intent = custom_logic_on_transcripts(
                        transcripts, intents, intent_not_in, mutate_to
                    )
                    if mutated_intent[0].name == intents[0].name:
                        continue
                    else:
                        intents[0].name = mutated_intent[0].name
                        return intents
                else:
                    continue

            else:
                continue

        return intents

    def mutate_entity(
        self,
        intents: List[Intent],
        current_state: str,
        entities: List[BaseEntity],
    ) -> List[BaseEntity]:
        pass
        # for rule in self.rules:
        #     conditions = self.rules['conditions']

    # def mutate_original_intent(
    #     self,
    #     current_intents: List[Intent],
    # ):
    #     pass

    @staticmethod
    def handle_entity_cases(
        entities: List[BaseEntity],
        intents: List[Intent],
        mutate_to: str,
        entity_entitytype_in: Union[List[str], None],
        entity_type_in: Union[List[str], None],
        entity_value_in: Union[List[str], None],
        entity_dim_in: Union[List[str], None],
    ) -> List[Intent]:

        intents_copy = copy.deepcopy(intents)

        if entity_type_in and entity_value_in:
            for ent_type_in in entity_type_in:
                for ent_value_in in entity_value_in:
                    if ent_type_in in [x.type for x in entities]:
                        if ent_value_in in [x.value for x in entities]:
                            intents_copy[0].name = mutate_to
                            return intents_copy

        if entity_dim_in:
            for ent_dim_in in entity_dim_in:
                if ent_dim_in in [x.dim for x in entities]:
                    intents_copy[0].name = mutate_to
                    return intents_copy

        if entity_type_in:
            for ent_type_in in entity_type_in:
                if ent_type_in in [x.type for x in entities]:
                    intents_copy[0].name = mutate_to
                    return intents_copy

        if entity_entitytype_in:
            for ent_enttype_in in entity_entitytype_in:
                if ent_enttype_in in [x.entity_type for x in entities]:
                    intents_copy[0].name = mutate_to
                    return intents_copy

        return intents_copy

    # The below static methods are helper methods coming from ashley's StateToIntent code wherein we need to count the number of digits and check if a number is present in more than 50% of transcripts

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


def test_intent_entity_plugin(name, rules, current_state, previous_intent):
    entity_dict = {
        "type": "fee_waiver",
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
    "type": "fee_waiver",
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
    "score": "",
    # newly added attributes
    "dim": "extra_baggage_intent",
    "latent": True,
    "range": {"start": 0, "end": 0},
    # "start": 0,
    # "end": 0,
    "body": "",
}
