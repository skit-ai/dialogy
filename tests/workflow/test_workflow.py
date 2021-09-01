import json
from typing import Any, Optional

import pandas as pd
import pytest
from sklearn.metrics import f1_score

import dialogy.constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.plugins import MergeASROutputPlugin
from dialogy.types import Intent
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
        w.input = v

    workflow = Workflow(
        [MergeASROutputPlugin(access=lambda w: w.input, mutate=m, debug=True)],
        debug=True,
    )
    workflow.run(input_=["apples"])
    assert workflow.input == ["<s> apples </s>"], "workflow.output should == 'apples'."
    workflow.flush()
    assert workflow.input == {}
    assert workflow.output == {const.INTENTS: [], const.ENTITIES: []}


def test_workflow_prediction_labels() -> None:
    def modify_input(w, v):
        w.input[const.CLASSIFICATION_INPUT] = v

    def modify_output(w, v):
        w.output[const.INTENTS] = v

    class MockClassificationPlugin(Plugin):
        def __init__(
            self,
            access: Optional[PluginFn] = None,
            mutate: Optional[PluginFn] = None,
            debug: bool = False,
        ) -> None:
            super().__init__(access, mutate, debug=debug)

        def inference(self, text):
            return [Intent(name="_error_", score=1)]

        def utility(self, *args: Any) -> Any:
            return self.inference(*args)

    workflow = Workflow(
        [
            MockClassificationPlugin(
                access=lambda w: w.input[const.CLASSIFICATION_INPUT],
                mutate=modify_output,
                debug=True,
            )
        ],
        debug=True,
    )

    test_df = pd.DataFrame(
        [
            {
                "id": 1,
                "data": json.dumps({"alternatives": [[{"transcript": "yes"}]]}),
                "labels": "_confirm_",
            },
            {
                "id": 2,
                "data": json.dumps({"alternatives": [[{"transcript": "no"}]]}),
                "labels": "_cancel_",
            },
        ]
    )

    report_df: pd.DataFrame = workflow.prediction_labels(test_df, id_="id")
    result = pd.merge(test_df, report_df, on="id")
    score = f1_score(
        result[const.LABELS],
        result[const.INTENT],
        zero_division=0,
        average="micro",
    )
    assert score == 0


def test_workflow_as_dict():
    """
    We can serialize a workflow.
    """
    workflow = Workflow()
    assert workflow.json() == {
        "input": {},
        "output": {const.INTENTS: [], const.ENTITIES: []},
    }
