from typing import List, Dict, Callable
from dialogy.workflow import Workflow
from dialogy.types.utterances import Utterance


PluginFn = Callable[[Workflow], None]
GetWorkflowUtteranceFn = Callable[[Workflow], List[Utterance]]
UpdateWorkflowStringFn = Callable[[Workflow, str], None]
