"""
Module provides access to pre-defined plugin types.

Import Types:
    - PluginFn
    - GetWorkflowUtteranceFn
    - UpdateWorkflowStringFn
"""
from typing import Any, Callable, List

from dialogy.types.utterances import Utterance
from dialogy.workflow import Workflow

PluginFn = Callable[..., Any]
GetWorkflowUtteranceFn = Callable[[Workflow], List[Utterance]]
UpdateWorkflowStringFn = Callable[[Workflow, str], None]
