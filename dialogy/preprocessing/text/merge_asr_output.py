"""
Module provides access to a Plugin to combine ASR output.

Since ASR outputs may contain n-best transcripts, the plugins here provide strategies
to unify these into one.

Import functions:
    - merge_asr_output
"""
from typing import List
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
    """
    Create a closure for single text representation for ASR output.

    This Plugin provides a merging strategy for n-best ASR transcripts.

    Args:
        access (GetWorkflowUtteranceFn): Function to access workflow elements.
        mutate (UpdateWorkflowStringFn): Function to modify workflow elements.

    Returns:
        PluginFn: Closure function returned
    """

    def inner(workflow: Workflow) -> None:
        """
        Join ASR output to single string.

        This function provides a merging strategy for n-best ASR transcripts by
        joining each transcript, such that:
            - each sentence end is marked by "</s>" and,
            - sentence start marked by "<s>".

        The key "transcript" is expected in the ASR output, the value of which would be operated on
        by this function.

        Example:
            input: [{"transcript": "This is a sentence"}, {"transcript": "That is a sentence"}]
            output: "<s> This is a sentence </s> <s> That is a sentence </s>"

        Args:
            workflow (Workflow): Model pipeline to read and modify.

        Raises:
            KeyError: `transcript` is a necessary key in ASR output. If missing, KeyError is raised.
        """
        utterances: List[Utterance] = access(workflow)

        try:
            flat_representation: List[str] = [
                alternative["transcript"]
                for utterance in utterances
                for alternative in utterance
                if isinstance(alternative["transcript"], str)
            ]
        except KeyError as key_error:
            raise KeyError("`transcript` is expected in the ASR output.") from key_error

        merged_string = "<s> " + " </s> <s> ".join(flat_representation) + " </s>"
        mutate(workflow, merged_string)

    return inner
