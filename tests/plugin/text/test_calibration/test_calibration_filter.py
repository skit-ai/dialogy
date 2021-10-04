# type : ignore

import json
from copy import copy
from typing import ValuesView

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from dialogy import constants as const
from dialogy.plugins.text.calibration.xgb import CalibrationModel
from dialogy.workflow.workflow import Workflow
from tests import EXCEPTIONS, load_tests

json_data = load_tests("df", __file__, ext=".json")
df = pd.DataFrame(json_data, columns=["conv_id", "data", "tag", "value", "time"])


def access(workflow):
    return workflow.input


def mutate(workflow, value):
    workflow.output = value


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

calibration_model = CalibrationModel(
    access=access, mutate=mutate, threshold=float("inf"), input_column="data", model_name="temp.pkl"
)
calibration_model.train(df)


def test_calibration_model_predict():
    alternatives = json.loads(df.iloc[0]["data"])[0]
    assert np.allclose(
        calibration_model.predict(alternatives), np.array([0.14196964]), atol=1e-5
    )


def test_calibration_model_filter_asr_output():
    alternatives = json.loads(df.iloc[0]["data"])
    assert (
        calibration_model.filter_asr_output(alternatives)
        == alternatives
    )
    calibration_model.threshold = float("-inf")
    assert calibration_model.filter_asr_output(alternatives) == [[]]


def test_calibration_model_transform():
    assert calibration_model.transform(df).equals(df.drop("use", axis=1))
    json_data_no_scores = copy(json_data)
    json_data_no_scores[0][1] = json.dumps({"alternatives": [[{"transcript": "yes"}]]})
    df_no_scores = pd.DataFrame(
        json_data_no_scores, columns=["conv_id", "data", "tag", "value", "time"]
    )
    assert (calibration_model.transform(df_no_scores).iloc[0]).equals(
        df_no_scores.drop("use", axis=1).iloc[1]
    )

    json_data_empty_asr_output = copy(json_data)
    json_data_empty_asr_output[0][1] = "[]"
    df_empty_asr_output = pd.DataFrame(
        json_data_empty_asr_output, columns=["conv_id", "data", "tag", "value", "time"]
    )
    assert (
        calibration_model.transform(df_empty_asr_output)
        .iloc[0]
        .equals(df_empty_asr_output.drop("use", axis=1).iloc[1])
    )


def test_calibration_model_validation():
    assert calibration_model.validate(df)
    json_data[0][2] = '[{"type": "_cancel_", "value": true}]'
    assert not calibration_model.validate(
        pd.DataFrame(json_data, columns=["conv_id", "data", "tag", "value", "time"])
    )


def test_calibration_model_utility():
    assert calibration_model.utility(
        [[{"transcript": "hello", "am_score": -100, "lm_score": -200}]]
    ) == ["hello"]
    calibration_model.threshold = float("inf")
    assert (
        calibration_model.utility(
            [
                [
                    {
                        "transcript": "hello world hello world",
                        "am_score": -100,
                        "lm_score": -200,
                    }
                ]
            ]
        )
        == ["hello world hello world"]
    )
