import pytest

from dialogy.base import Input, Output
from dialogy.types import Intent
from pydantic.error_wrappers import ValidationError


def test_invalid_reftime():
    with pytest.raises(ValueError):
        Input(utterances="test", reference_time=18**15)


def test_input_extension():
    instance = Input(
        utterances=[[{"transcript": "test"}]], reference_time=1644238676772
    )
    extended = Input.from_dict(
        {"utterances": [[{"transcript": "test"}]], "reference_time": 1644238676772}
    )
    assert instance == extended


def test_output_extension():
    intent = Intent(name="test", score=0.5)
    instance = Output(intents=[intent])
    extended = Output.from_dict({"intents": [intent]})
    assert instance == extended


def test_input_invalid_transcript_key():
    with pytest.raises(TypeError):
        Input(utterances=[[{"not_transcript": "hello world", "confidence": None}]])


def test_output_invalid_intents_type():
    with pytest.raises(ValidationError):
        Output(intents=1)


def test_output_invalid_intent_type():
    with pytest.raises(ValidationError):
        Output(intents=[1])


def test_output_invalid_entities_type():
    with pytest.raises(ValidationError):
        Output(entities=1)


def test_output_invalid_entity_type():
    with pytest.raises(ValidationError):
        Output(entities=[1])


def test_output_invalid_original_intent_type():
    with pytest.raises(ValidationError):
        Output(original_intent=1)


def test_output_invalid_original_intent_score():
    with pytest.raises(ValidationError):
        Output(original_intent={"score": "apples", "name": "test"})


def test_output_invalid_original_intent_name():
    with pytest.raises(TypeError):
        Output(original_intent={"name": 1, "score": 0.5})


def test_output_missing_original_intent_score():
    with pytest.raises(ValidationError):
        Output(original_intent={"name": "test"})


def test_output_missing_original_intent_name():
    with pytest.raises(ValidationError):
        Output(original_intent={"score": 0.5})
