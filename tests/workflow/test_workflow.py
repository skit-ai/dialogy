import pytest

import dialogy.constants as const
from dialogy.base import Input, Output
from dialogy.plugins import MergeASROutputPlugin
from dialogy.workflow import Workflow


def test_workflow_get_input() -> None:
    """
    Basic initialization.
    """
    workflow = Workflow([])
    assert workflow.input == None, "workflow is NoneType."


def test_workflow_set_output() -> None:
    """
    We can set output and input as anything.
    """
    workflow = Workflow([])
    workflow.output = 10
    assert workflow.output == 10, "workflow.get_output() should == 10."


def test_workflow_postprocessors_not_list_error() -> None:
    """
    postprocessrors should be of type [`PluginFn`](../../plugin/test_plugins.html).
    """
    with pytest.raises(TypeError):
        _ = Workflow(10)


def test_not_callable_pre_post_processors_type_error() -> None:
    workflow = Workflow([2, 3])

    with pytest.raises(TypeError):
        workflow.execute()


def test_workflow_history_logs() -> None:
    """
    We can execute the workflow.
    """
    workflow = Workflow(
        [MergeASROutputPlugin(dest="input.clf_feature", debug=True)],
        debug=True,
    )
    input_, _ = workflow.run(Input(utterances=["apples"]))
    assert input_["clf_feature"] == ["<s> apples </s>"]
    assert workflow.input == None
    assert workflow.output == Output()


def test_workflow_as_dict():
    """
    We can serialize a workflow.
    """
    workflow = Workflow()
    assert workflow.json() == {
        "input": None,
        "output": {const.INTENTS: [], const.ENTITIES: []},
    }
