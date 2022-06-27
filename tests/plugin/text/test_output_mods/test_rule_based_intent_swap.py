import pytest

from dialogy.base import Input, Output
from dialogy.plugins import RuleBasedIntentSwap
from dialogy.types import Intent
from dialogy.workflow import Workflow
from tests import load_tests


@pytest.mark.parametrize("test_case", load_tests("cases", __file__))
def test_rule_based_intent_swap(test_case):
    intents = [Intent(name=test_case["payload"]["intent"])]
    intents = RuleBasedIntentSwap(test_case["rules"], dest="output.intents").swap(test_case["payload"], intents)
    assert intents[0].name == test_case["expected"]


def test_rule_based_intent_swap_with_workflow():
    output: Output
    workflow = Workflow([
        RuleBasedIntentSwap([{
            "rename": "_collect_datetime_",
            "depends_on": {
                "state": "COLLECT_DATETIME"
            }
        }], dest="output.intents")
    ])

    workflow.set("output.intents", [Intent(name="_oos_")])
    workflow.set("output.entities", [])
    _, output = workflow.run(Input(utterances=[{"transcript": "tonight"}], current_state="COLLECT_DATETIME"))
    assert output["intents"][0]["name"] == "_collect_datetime_"
