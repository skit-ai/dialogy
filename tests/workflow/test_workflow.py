from typing import final
import pytest

import dialogy.constants as const
from dialogy.base import Input, Output, Plugin
from dialogy.plugins import MergeASROutputPlugin
from dialogy.workflow import Workflow
from dialogy.types import Intent


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
        "output": {const.INTENTS: [], const.ENTITIES: [], const.ORIGINAL_INTENT: {}},
    }


def test_workflow_set_path():
    workflow = Workflow()
    workflow.set("output.original_intent", {"name": "test", "score": 0.5})
    workflow_dict = workflow.json()
    assert workflow_dict["output"]["original_intent"] == {"name": "test", "score": 0.5}


def test_workflow_invalid_set_path():
    """
    We can't set invalid values in workflow.
    """
    workflow = Workflow()
    with pytest.raises(ValueError):
        workflow.set("invalid.path", [])


def test_workflow_invalid_set_attribute():
    """
    We can't set invalid values in workflow.
    """
    workflow = Workflow()
    with pytest.raises(ValueError):
        workflow.set("output.invalid", [])


def test_workflow_invalid_set_value():
    """
    We can't set invalid values in workflow.
    """
    workflow = Workflow()
    with pytest.raises(ValueError):
        workflow.set("output.intents", 10)


def test_safe_flush():
    workflow = Workflow()
    i, o = workflow.flush()
    assert i == {}
    assert o == {}


def test_flush_on_exception():
    class FailingPlugin(Plugin):
        def __init__(self, dest: str = None, debug: bool = False) -> None:
            super().__init__(dest=dest, debug=debug)

        def utility(self, _: Input, _o: Output) -> int:
            return 0/0

    workflow = Workflow([FailingPlugin()])
    workflow.set("output.intents", [Intent(name="test", score=0.5)])
    try:
        workflow.run(Input(utterances=["apples"]))
    except ZeroDivisionError:
        pass
    finally:
        assert workflow.output == Output()
        assert workflow.input == None
