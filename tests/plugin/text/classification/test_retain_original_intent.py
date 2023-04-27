from dialogy.base import Input, Output
from dialogy.plugins.registry import RetainOriginalIntentPlugin
from dialogy.types import Intent
from dialogy.workflow import Workflow


def test_retain_original_intent():
    plugin = RetainOriginalIntentPlugin()
    output = Output(intents=[Intent(name="test", score=0.5)])
    workflow = Workflow([plugin])
    _, output = workflow.run(Input(utterances=[[{"transcript": "test"}]]), output)
    assert output.original_intent == {"name": "test", "score": 0.5}


def test_retain_original_intent_with_no_intents():
    plugin = RetainOriginalIntentPlugin()
    assert plugin.retain([]) == {}
