"""
This is a tutorial for understanding the use of `VotePlugin`.
"""
from typing import Any, List

import pytest

from dialogy import constants as const
from dialogy.plugins import VotePlugin
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
    vote_plugin = VotePlugin(access=lambda w: (w.output[0], 0), mutate=update_intent)()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == const.S_INTENT_OOS


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
        debug=True, access=lambda w: (w.output[0], len(intents)), mutate=update_intent
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == "a"


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
        access=lambda w: (w.output[0], len(intents)), mutate=update_intent
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == "_oos_"


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
        access=lambda w: (w.output[0], len(intents)), mutate=update_intent
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == "_oos_"


def test_missing_access():
    intents = [
        Intent(name="a", score=0.3),
        Intent(name="a", score=0.2),
        Intent(name="b", score=0.1),
        Intent(name="b", score=0.1),
    ]

    vote_plugin = VotePlugin(mutate=update_intent)()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    with pytest.raises(TypeError):
        intent, _ = workflow.run(input_="")


def test_missing_mutate():
    intents = [
        Intent(name="a", score=0.3),
        Intent(name="a", score=0.2),
        Intent(name="b", score=0.1),
        Intent(name="b", score=0.1),
    ]

    vote_plugin = VotePlugin(access=lambda w: w.output[0])()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    with pytest.raises(TypeError):
        intent, _ = workflow.run(input_="")


def test_representation_oos():
    intents = [
        Intent(name="a", score=0.99),
        Intent(name="b", score=0.1),
        Intent(name="b", score=0.4),
        Intent(name="b", score=0.31),
        Intent(name="d", score=0.44),
    ]

    vote_plugin = VotePlugin(
        access=lambda w: (w.output[0], len(intents)), mutate=update_intent
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == "_oos_"


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
        access=lambda w: (w.output[0], len(intents)), mutate=update_intent
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []
    intent, _ = workflow.run(input_="")
    assert intent.name == "a"


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
        access=lambda w: (w.output[0], len(intents)),
        mutate=update_intent,
        aggregate_fn=5,
    )()
    workflow = Workflow(preprocessors=[], postprocessors=[vote_plugin])
    workflow.output = intents, []

    with pytest.raises(TypeError):
        intent, _ = workflow.run(input_="")
        assert intent.name == "a"
