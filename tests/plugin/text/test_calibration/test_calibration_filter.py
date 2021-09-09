import json
from typing import ValuesView

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from dialogy import constants as const
from dialogy.plugins.text.calibration.xgb import CalibrationModel
from dialogy.workflow.workflow import Workflow
from tests import EXCEPTIONS, load_tests

df = pd.DataFrame(
    json.load(open("test_df.json")), columns=["conv_id", "data", "tag", "value", "time"]
)


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

calibration_model = CalibrationModel(threshold=1.0)
calibration_model.train(df, "temp.pkl")


def test_calibration_model_inference():
    alternatives = json.loads(df.iloc[0]["data"])["alternatives"][0]
    assert calibration_model.inference(alternatives) == pytest.approx(0.14)


def test_calibration_model_filter_asr_output():
    alternatives = json.loads(df.iloc[0]["data"])
    assert calibration_model.filter_asr_output(alternatives) == alternatives
    calibration_model.threshold = float("-inf")
    assert calibration_model.filter_asr_output(alternatives) == {"alternatives": [[]]}


def test_calibration_model_transform():
    # load intent tagging data here.
    assert calibration_model.transform(df).equals(df.drop("use", axis=1))
