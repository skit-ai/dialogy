"""
Module provides access to pre-defined plugin types.

Import Types:
    - PluginFn
    - GetWorkflowUtteranceFn
    - UpdateWorkflowStringFn
"""
from typing import List, Callable, Any
from dialogy.workflow import Workflow
from dialogy.types.utterances import Utterance

PluginFn = Callable[..., Any]
GetWorkflowUtteranceFn = Callable[[Workflow], List[Utterance]]
UpdateWorkflowStringFn = Callable[[Workflow, str], None]
