from typing import List, Dict, Callable


def merge_asr_output(get_utterance: Callable, set_input: Callable):
    def inner(workflow):
        utterances: List[List[Dict]] = get_utterance(workflow)
        flat_representation = [alternatives["transcript"]
                               for utterance in utterances for alternatives in utterance]
        merged_string = "<s> " + \
            " </s> <s> ".join(flat_representation) + " </s>"
        set_input(workflow, merged_string)
    return inner
