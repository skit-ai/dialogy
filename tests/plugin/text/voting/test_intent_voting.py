"""
This is a tutorial for understanding the use of `VotePlugin`.
"""
from typing import List

import pytest

from dialogy import constants as const
from dialogy.plugins import VotePlugin
from dialogy.base import Input, Output
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow


def update_intent(workflow, value):
    _, entities = workflow.output
    workflow.output = (value, entities)


def test_voting_0_intents():
    """
    The code uses division. So its always good to
    have a test to see if it takes care of division 0.
    """
    intents: List[Intent] = []
    vote_plugin = VotePlugin(dest="output.intents")
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == const.S_INTENT_OOS


def test_voting_n_intents():
    """
    Testing the usual case.
    """
    intents = [
        Intent(name="a", score=1),
        Intent(name="a", score=1),
        Intent(name="b", score=0.13),
        Intent(name="a", score=1),
    ]
    vote_plugin = VotePlugin(
        debug=False, dest="output.intents",
    )
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == "a"


def test_voting_on_conflicts():
    """
    Testing the case with conflicts.
    """
    intents = [
        Intent(name="a", score=1),
        Intent(name="a", score=1),
        Intent(name="b", score=1),
        Intent(name="b", score=1),
    ]
    vote_plugin = VotePlugin(
        dest="output.intents"
    )
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == "_oos_"


def test_voting_on_weak_signals():
    """
    Testing all weak intents.
    """
    intents = [
        Intent(name="a", score=0.3),
        Intent(name="a", score=0.2),
        Intent(name="b", score=0.1),
        Intent(name="b", score=0.1),
    ]
    vote_plugin = VotePlugin(
        dest="output.intents"
    )
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == "_oos_"


def test_representation_oos():
    intents = [
        Intent(name="a", score=0.99),
        Intent(name="b", score=0.1),
        Intent(name="b", score=0.4),
        Intent(name="b", score=0.31),
        Intent(name="d", score=0.44),
    ]

    vote_plugin = VotePlugin(dest="output.intents")
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == "_oos_"


def test_representation_intent():
    intents = [
        Intent(name="a", score=0.99),
        Intent(name="a", score=0.99),
        Intent(name="a", score=0.91),
        Intent(name="b", score=0.1),
        Intent(name="c", score=0.31),
        Intent(name="d", score=0.44),
    ]

    vote_plugin = VotePlugin(
        dest="output.intents"
    )
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)
    _, output = workflow.run(Input(utterances=["some text"]))
    assert output["intents"][0]["name"] == "a"


def test_aggregate_fn_incorrect():
    intents = [
        Intent(name="a", score=0.99),
        Intent(name="a", score=0.99),
        Intent(name="a", score=0.91),
        Intent(name="b", score=0.1),
        Intent(name="c", score=0.31),
        Intent(name="d", score=0.44),
    ]

    vote_plugin = VotePlugin(
        dest="output.intents",
        aggregate_fn=5,
    )
    workflow = Workflow([vote_plugin])
    workflow.output = Output(intents=intents)

    with pytest.raises(TypeError):
        _, output = workflow.run(Input(utterances=[""]))
        assert output["intents"][0]["name"] == "a"
