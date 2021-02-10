"""
Module provides access to a Plugin to combine ASR output.

## Tutorial

- [merge_asr_output](../../../tests/preprocess/text/test_merge_asr_output.html)

Import functions:

- merge_asr_output
"""
from typing import List
from dialogy.workflow import Workflow
from dialogy.types.plugin import (
    GetWorkflowUtteranceFn,
    UpdateWorkflowStringFn,
    PluginFn,
)
from dialogy.types.utterances import Utterance


# == merge_asr_output ==
def merge_asr_output(utterances: List[Utterance]) -> str:
    """
    Join ASR output to single string.

    This function provides a merging strategy for n-best ASR transcripts by
    joining each transcript, such that:

    - each sentence end is marked by " &lt;/s&gt;" and,
    - sentence start marked by " &lt;s&gt;".


    The key "transcript" is expected in the ASR output, the value of which would be operated on
    by this function.

    Example:
    ```python

    input = [
        {"transcript": "This is a sentence"},
        {"transcript": "That is a sentence"}
    ]

    "<s> This is a sentence </s> <s> That is a sentence </s>"
    ```

    Args:

    - utterances (`List[Utterance]`): ASR transcriptions


    Raises:

    - KeyError: Missing key `"transcript"` within alternatives.


    Returns:

    - str: concatenated ASR transcripts into a string.
    """
    try:
        flat_representation: List[str] = [
            alternative["transcript"]
            for utterance in utterances
            for alternative in utterance
            if isinstance(alternative["transcript"], str)
        ]
    except KeyError as key_error:
        raise KeyError("`transcript` is expected in the ASR output.") from key_error

    return "<s> " + " </s> <s> ".join(flat_representation) + " </s>"


# ---

# == merge_asr_output_plugin ==
def merge_asr_output_plugin(
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
        Uses the `merge_asr_output` to build the plugin.

        Args:
        - workflow (Workflow):
        """
        merged_string = merge_asr_output(access(workflow))
        mutate(workflow, merged_string)

    return inner
