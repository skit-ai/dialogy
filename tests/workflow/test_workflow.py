import pytest

from dialogy.plugins import MergeASROutputPlugin
from dialogy.workflow import Workflow


def test_workflow_get_input() -> None:
    """
    Basic initialization.
    """
    workflow = Workflow([])
    assert workflow.input == {}, "workflow.get_input() is a dict()."


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
        _ = Workflow(10)  # type: ignore


def test_not_callable_pre_post_processors_type_error() -> None:
    workflow = Workflow([2, 3])  # type: ignore

    with pytest.raises(TypeError):
        workflow.execute()


def test_workflow_history_logs() -> None:
    """
    We can execute the workflow.
    """

    def m(w, v):
        w.output = v

    workflow = Workflow(
        [MergeASROutputPlugin(access=lambda w: w.input, mutate=m, debug=True)],
        debug=True,
    )
    workflow.run(input_=["apples"])
    assert workflow.output == ["<s> apples </s>"], "workflow.output should == 'apples'."
    workflow.flush()
    assert workflow.input == {}
    assert workflow.output == {}
