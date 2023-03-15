import yaml
from dialogy.plugins.text.intent_entity_mutator import IntentEntityMutatorPlugin
from dialogy.workflow import Workflow
from dialogy.types import Intent, BaseEntity
from dialogy.base.plugin import Input, Output
from typing import List, Any, Dict, Union



def intent_mutation(
    intent_name,
    rules,
    current_state,
    previous_intent,
    entity_dict,
    transcript,
    mutate_val,
):

    if entity_dict:
        entity = BaseEntity.from_dict(entity_dict)
    intent_entity = IntentEntityMutatorPlugin(rules=rules)
    workflow = Workflow([intent_entity])
    intent = Intent(name=intent_name, score=0.4)

    body = [[{"transcript": transcript}]]
    inp = Input(
        utterances=body, current_state=current_state, previous_intent=previous_intent
    )
    if entity_dict:
        out = Output(intents=[intent], entities=[entity])
    else:
        out = Output(intents=[intent])
    _, out = workflow.run(inp, out)
    assert out.intents[0].name == mutate_val


def test_intent_mutation_cases():
    with open("tests/intent_entity_mutator/mutate_intent.yaml", "r") as f:
        rules = yaml.load(f, Loader=yaml.Loader)

    with open("tests/intent_entity_mutator/test_cases_intent.yaml", "r") as f:
        test_cases = yaml.load(f, Loader=yaml.Loader)["test_cases"]

    for case in test_cases:
        intent_name = case["intent_name"]
        current_state = case["current_state"]
        transcript = case["transcript"]
        entity_dict = case["entity_dict"]
        previous_intent = case["previous_intent"]
        mutate_val = case["mutate_val"]

        intent_mutation(
            intent_name,
            rules,
            current_state,
            previous_intent,
            entity_dict,
            transcript,
            mutate_val,
        )
