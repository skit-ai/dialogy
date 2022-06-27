from dialogy.base import Input
from dialogy.plugins import RetainOriginalIntentPlugin
from dialogy.types import Intent
from dialogy.workflow import Workflow


def test_retain_original_intent():
    plugin = RetainOriginalIntentPlugin()
    workflow = Workflow([plugin])
    workflow.set("output.intents", [Intent(name="test", score=0.5)])
    _, output = workflow.run(Input(utterances=["test"]))
    assert output["original_intent"] == {"name": "test", "score": 0.5}


def test_retain_original_intent_with_no_intents():
    plugin = RetainOriginalIntentPlugin()
    assert plugin.retain([]) == {}