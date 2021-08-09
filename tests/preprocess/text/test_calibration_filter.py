from dialogy.plugins.preprocess.text.calibration import (
    predict_alternative,
    filter_asr_output,
)
import numpy as np
from scipy import sparse


class MyVectorizer(object):
    def __init__(self):
        pass

    def transform(self, text):
        assert isinstance(text, list)
        return sparse.csr_matrix(np.array([1]))


class MyClassifier(object):
    def __init__(self):
        pass

    def predict(self, X):
        return np.array([1])


vectorizer = MyVectorizer()
classifier = MyClassifier()


def test_predict_alternative() -> None:
    assert (
        predict_alternative(
            {"transcript": "hello world", "am_score": 200, "lm_score": 100},
            vectorizer,
            classifier,
        )
        == 1
    )


def test_filter_asr_output() -> None:
    asr_output = [
        [
            {"transcript": "hello world", "am_score": 200, "lm_score": 100},
            {"transcript": "yes", "am_score": 300, "lm_score": 400},
        ]
    ]

    assert filter_asr_output(asr_output, 1.5, vectorizer, classifier) == (
        asr_output,
        [1, 1],
    )
    assert filter_asr_output(asr_output, 0.5, vectorizer, classifier) == ([[]], [1, 1])

    asr_output = [
        [
            {"transcript": "hello world", "am_score": 200, "lm_score": 100},
            {"transcript": "yes", "am_score": 300, "lm_score": 400},
        ],
        [
            {"transcript": "hello world", "am_score": 200, "lm_score": 100},
            {"transcript": "yes", "am_score": 300, "lm_score": 400},
        ],
    ]
    assert filter_asr_output(asr_output, 1.5, vectorizer, classifier) == (
        asr_output,
        [1, 1, 1, 1],
    )
    assert filter_asr_output(asr_output, 0.5, vectorizer, classifier) == (
        [[], []],
        [1, 1, 1, 1],
    )
