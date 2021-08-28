import numpy as np
import pytest
from scipy import sparse

from dialogy import constants as const
from dialogy.plugins.text.calibration import WERCalibrationConfig, WERCalibrationPlugin
from dialogy.workflow.workflow import Workflow
from tests import EXCEPTIONS, load_tests


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


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_calibration(payload):
    body = payload["input"]
    expected = payload.get("expected")
    # exception = payload.get("exception")
    config = payload.get("config") or {}
    lang = payload.get("lang")
    mock = payload.get("mock")
    threshold = payload.get("threshold")

    def access(_):
        return body, lang

    def mutate(workflow, value):
        workflow.input = value

    wer_calibration = WERCalibrationPlugin(config, access=access, mutate=mutate)
    if mock:
        wer_calibration.config[lang] = WERCalibrationConfig(
            vectorizer=vectorizer, classifier=classifier, threshold=threshold
        )
    workflow = Workflow([wer_calibration])
    workflow.run(input_=body)

    assert workflow.input == expected[const.ALTERNATIVES]
