from typing import final

import pytest

import dialogy.constants as const
from dialogy.base import Input, Output, Plugin
from dialogy.plugins import MergeASROutputPlugin
from dialogy.types import Intent
from dialogy.workflow import Workflow


def test_workflow_postprocessors_not_list_error() -> None:
    """
    postprocessrors should be of type [`PluginFn`](../../plugin/test_plugins.html).
    """
    with pytest.raises(TypeError):
        _ = Workflow(10)


def test_workflow_history_logs() -> None:
    """
    We can execute the workflow.
    """
    workflow = Workflow(
        [MergeASROutputPlugin(dest="input.clf_feature", debug=True)],
        debug=True,
    )
    input_, _ = workflow.run(Input(utterances=[[{"transcript": "apples"}]]))
    assert input_.clf_feature == ["<s> apples </s>"]
    