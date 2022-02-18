import pytest

from dialogy.base import Input, Output
from dialogy.types import Intent


def test_invalid_reftime():
    with pytest.raises(ValueError):
        Input(utterances="test", reference_time=18 ** 15)


def test_input_extension():
    instance = Input(utterances="test", reference_time=1644238676772)
    extended = Input.from_dict({"utterances": "test", "reference_time": 1644238676772})
    assert instance == extended


def test_output_extension():
    intent = Intent(name="test", score=0.5)
    instance = Output(intents=[intent])
    extended = Output.from_dict({"intents": [intent]})
    assert instance == extended


def test_output_invalid_intents_type():
    with pytest.raises(TypeError):
        Output(intents=1)


def test_output_invalid_intent_type():
    with pytest.raises(TypeError):
        Output(intents=[1])


def test_output_invalid_entities_type():
    with pytest.raises(TypeError):
        Output(entities=1)


def test_output_invalid_entity_type():
    with pytest.raises(TypeError):
        Output(entities=[1])
