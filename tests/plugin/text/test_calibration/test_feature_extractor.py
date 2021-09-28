# type : ignore

import json
from copy import copy

import numpy as np
import pandas as pd

from dialogy.plugins.text.calibration.xgb import FeatureExtractor
from tests import load_tests

mock_data = load_tests("df", __file__, ext=".json")
df = pd.DataFrame(mock_data, columns=["conv_id", "data", "tag", "value", "time"])

feature_extractor = FeatureExtractor()


def test_feature_extractor_fit():
    feature_extractor.fit(df)


# pre-calculated values
def test_feature_extractor_features():
    alternative = json.loads(df.iloc[0]["data"])["alternatives"][0]
    assert feature_extractor.features(alternative) == [
        [
            0.3889910975917115,
            0.3889910975917115,
            0.3889910975917115,
            0.3889910975917115,
            0.49338588343402934,
            0.0,
            0.3889910975917115,
            0.0,
            -47.20907571428571,
            19.145534285714287,
            0,
            7,
            -158.91936530855375,
            64.44939052806247,
            -124.90347396521894,
            -124.90347396521894,
        ]
    ]
    mock_data_null_alternatives = copy(mock_data)
    mock_data_null_alternatives[0][1] = json.dumps([[{"transcript": "hello"}]])
    mock_data_df_null_alternatives = pd.DataFrame(
        mock_data, columns=["conv_id", "data", "tag", "value", "time"]
    )
    try:
        assert feature_extractor.features(
            json.loads(mock_data_df_null_alternatives.iloc[0]["data"])["alternatives"][
                0
            ]
        )
        assert False
    except Exception:
        assert True


def test_feature_extractor_transform():
    assert np.allclose(
        feature_extractor.transform(df)[0],
        np.array(
            [
                [
                    0.3889911,
                    0.3889911,
                    0.3889911,
                    0.3889911,
                    0.49338588,
                    0.0,
                    0.3889911,
                    0.0,
                    -47.20907571,
                    19.14553429,
                    0.0,
                    7.0,
                    -158.91936531,
                    64.44939053,
                    -124.90347397,
                    -124.90347397,
                ],
                [
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    0.0,
                    1.0,
                    -161.56203,
                    72.6848,
                    0.0,
                    1.0,
                    -233.08473948,
                    104.86200051,
                    -161.56203,
                    -161.56203,
                ],
            ]
        ),
        atol=1e-6,
    )
    assert feature_extractor.transform(df)[1] == [0.14285714285714285, 0.0]
