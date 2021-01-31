import pytest
from dialogy.workflow import Workflow
from dialogy.preprocess.text.merge_asr_output import merge_asr_output


def test_merge_as_output():
    def access(workflow):
        return workflow.input

    def mutate(workflow, value):
        workflow.input = value

    workflow = Workflow(
        preprocessors=[merge_asr_output(access, mutate)], postprocessors=[]
    )

    workflow.run([[{"transcript": "hello world", "confidence": None}]])
    assert workflow.input == "<s> hello world </s>"


def test_merge_keyerror_on_missing_transcript():
    def access(workflow):
        return workflow.input

    def mutate(workflow, value):
        workflow.input = value

    workflow = Workflow(
        preprocessors=[merge_asr_output(access, mutate)], postprocessors=[]
    )

    with pytest.raises(KeyError):
        workflow.run([[{"not_transcript": "hello world", "confidence": None}]])
