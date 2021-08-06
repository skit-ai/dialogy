from typing import Any, List, Dict
from dialogy import constants
import math
import numpy as np


def predict_alternative(
    alternative: Dict[str, Any], vectorizer: Any, classifier: Any
) -> float:
    vec_ = (
        vectorizer.transform([alternative[constants.TRANSCRIPT]]).todense().tolist()[0]
    )
    n_words = len(alternative[constants.TRANSCRIPT].split())
    am_score = alternative[constants.AM_SCORE]
    lm_score = alternative[constants.LM_SCORE]
    features = [
        am_score / n_words,
        lm_score / n_words,
        alternative[constants.TRANSCRIPT].count("UNK"),
        n_words,
        am_score / math.log(1 + n_words),
        lm_score / math.log(1 + n_words),
        am_score / math.sqrt(n_words),
        lm_score / math.sqrt(n_words),
    ]
    return classifier.predict(np.array([vec_ + features])).tolist()[0]


# == filter_asr_output ==
def filter_asr_output(
    utterances: List[List[Dict[str, Any]]],
    threshold: float,
    vectorizer: Any,
    classifier: Any,
) -> List[List[Dict[str, Any]]]:
    """
    .. _filter_asr_output:

    Filter ASR output to return `good` alternatives.

    This functions returns the good alternatives in the same format as the input.
    The good alternatives are decided if the pWER (predicted WER) is less than
    `threshold`.

    .. ipython:: python

        from dialogy.plugins.preprocess.text.calibration import filter_asr_output

        utterances = [[{"transcript": "This is a sentence", "am_score":230, "lm_score":100}, \
                            {"transcript": "This is another sentence", "am_score":230, "lm_score":100}]]
        filter_asr_output(utterances)

    :param utterances: A structure representing ASR output. We support only:

        1. :code:`List[List[Dict[str, Any]]]`

    :type utterances: List[List[Dict[str, Any]]]
    :return: Good alternatives.
    :rtype: List[List[Dict[str, Any]]]
    :raises: `AssertionError` if utterance isn't in the desired format.
    """

    valid_alternatives = []
    for utterance in utterances:
        res = []
        for alternative in utterance:
            pred_wer = predict_alternative(alternative, vectorizer, classifier)
            if pred_wer < threshold:
                res.append(alternative)
        valid_alternatives.append(res)
    return valid_alternatives
