from typing import List, Dict, Callable


def merge_asr_output(access: Callable, mutate: Callable):
    def inner(workflow):
        utterances: List[List[Dict]] = access(workflow)
        flat_representation = [alternatives["transcript"]
                               for utterance in utterances for alternatives in utterance]
        merged_string = "<s> " + \
            " </s> <s> ".join(flat_representation) + " </s>"
        mutate(workflow, merged_string)
    return inner
