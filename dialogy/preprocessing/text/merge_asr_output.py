from typing import List, Dict, Callable
from dialogy.workflow import Workflow
from dialogy.types.plugins import (
    GetWorkflowUtteranceFn,
    UpdateWorkflowStringFn,
    PluginFn,
)
from dialogy.types.utterances import Utterance


def merge_asr_output(
    access: GetWorkflowUtteranceFn, mutate: UpdateWorkflowStringFn
) -> PluginFn:
    def inner(workflow: Workflow) -> None:
        utterances: List[Utterance] = access(workflow)

        flat_representation: List[str] = [
            alternative["transcript"]
            for utterance in utterances
            for alternative in utterance
            if isinstance(alternative["transcript"], str)
        ]

        merged_string = "<s> " + " </s> <s> ".join(flat_representation) + " </s>"

        mutate(workflow, merged_string)

    return inner
