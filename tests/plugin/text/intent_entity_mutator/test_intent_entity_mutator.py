import pytest
import yaml

from dialogy.base.plugin import Input, Output
from dialogy.plugins.text.intent_entity_mutator import IntentEntityMutatorPlugin
from dialogy.types import BaseEntity, Intent
from dialogy.workflow import Workflow
from tests import load_tests

with open("tests/plugin/text/intent_entity_mutator/mutation_rules.yaml", "r") as f:
    rules = yaml.safe_load(f)


async def mutation(
    intent_name,
    rules,
    current_state,
    previous_intent,
    entity_dict,
    transcript,
    mutate_val,
    mutate,
):

   
    intent_entity = IntentEntityMutatorPlugin(rules=rules, replace_output=True)
    workflow = Workflow([intent_entity])
    intent = Intent(name=intent_name, score=0.4)

    body = [[{"transcript": transcript}]]
    inp = Input(
        utterances=body, current_state=current_state, previous_intent=previous_intent
    )
    if entity_dict:
        entity = BaseEntity.from_dict(entity_dict)
        out = Output(intents=[intent], entities=[entity])
    else:
        out = Output(intents=[intent])
    _, out = await workflow.run(inp, out)

    if isinstance(mutate_val, str):
        assert out.intents[0].name == mutate_val
    else:
        assert out.entities[0] == BaseEntity.from_dict(mutate_val)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", load_tests("mutation_cases", __file__))
def test_mutation_cases(payload):

    intent_name = payload["intent_name"]
    current_state = payload["current_state"]
    transcript = payload["transcript"]
    entity_dict = payload["entity_dict"]
    previous_intent = payload["previous_intent"]
    mutate_val = payload["mutate_val"]
    mutate = payload["mutate"]

    mutation(
        intent_name,
        rules,
        current_state,
        previous_intent,
        entity_dict,
        transcript,
        mutate_val,
        mutate,
    )


@pytest.mark.parametrize("payload", load_tests("mutation_rules", __file__))
def test_mutation_rules(payload):
    with pytest.raises(ValueError):
        intent_entity = IntentEntityMutatorPlugin(
            rules=payload, dest="output.intents", replace_output=True
        )
