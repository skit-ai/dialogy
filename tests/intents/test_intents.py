"""
Tests for intents
"""

from dialogy.types.intents import Intent
from dialogy.workflow import Workflow

def mock_plugin(_: Workflow) -> None:
    pass

def test_intent_parser():
    intent = Intent(
        name = "intent_name",
        score = 0.5
    )
    intent.add_parser(mock_plugin)

    assert intent.parsers == ["mock_plugin"]