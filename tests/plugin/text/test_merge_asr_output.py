import pytest

from dialogy.plugins import MergeASROutputPlugin
from dialogy.workflow import Workflow


def access(workflow):
    return workflow.input


def mutate(workflow, value):
    workflow.input = value


merge_asr_output_plugin = MergeASROutputPlugin(access=access, mutate=mutate)


def test_merge_asr_output() -> None:
    """
    This case shows the merge in case there is only one option.
    """

    workflow = Workflow([merge_asr_output_plugin])

    workflow.run([[{"transcript": "hello world", "confidence": None}]])
    assert workflow.input == ["<s> hello world </s>"]


def test_merge_longer_asr_output() -> None:
    """
    This case shows the merge in case there are multiple options.
    """
    workflow = Workflow([merge_asr_output_plugin])

    workflow.run(
        [
            [
                {"transcript": "hello world", "confidence": None},
                {"transcript": "hello word", "confidence": None},
                {"transcript": "jello world", "confidence": None},
            ]
        ]
    )
    assert workflow.input == [
        "<s> hello world </s> <s> hello word </s> <s> jello world </s>"
    ]


def test_merge_keyerror_on_missing_transcript() -> None:
    """
    This test, shows that `transcript` is an important key. If the asr has a different key, than `transcript`
    then this plugin would not work for you.
    """

    workflow = Workflow([merge_asr_output_plugin])

    with pytest.raises(TypeError):
        workflow.run([[{"not_transcript": "hello world", "confidence": None}]])
