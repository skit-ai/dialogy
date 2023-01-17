"""
This module was created in response to: https://github.com/Vernacular-ai/dialogy/issues/9
we will ship functions to assist normalization of ASR output, we will refer to these as Utterances.
"""
from typing import Any, List

import pytest

from dialogy.utils import normalize
from dialogy.utils.normalize_utterance import is_list_of_string

TEST_STRING = "hello world"
EXPECTED_OUTPUT = [TEST_STRING]


@pytest.mark.parametrize(
    "utterance,expected",
    [
        ([[{"transcript": TEST_STRING}]], EXPECTED_OUTPUT),
        ([{"transcript": TEST_STRING}], EXPECTED_OUTPUT),
        ([TEST_STRING], EXPECTED_OUTPUT),
    ],
)
def test_normalize_utterance(utterance: Any, expected: List[str]) -> None:
    output = normalize(utterance)
    assert output == expected


@pytest.mark.parametrize(
    "utterance",
    [1, [[{"teapot": TEST_STRING}]], [{"teapot": TEST_STRING}], [1, 2]],
)
def test_cant_normalize_utterance(utterance: Any) -> None:
    with pytest.raises(TypeError):
        _ = normalize(utterance)


@pytest.mark.parametrize(
    "utterance,expected",
    [
        ([[{"teapot": TEST_STRING}]], False),
        ([{"teapot": TEST_STRING}], False),
        ([1, 2], False),
        (1, False),
        (None, False),
    ],
)
def test_is_list_of_string(utterance: Any, expected: bool) -> None:
    output = is_list_of_string(utterance)
    assert output == expected
