"""
Trains a calibraation model. This contains two models:
- Vectorizer: TfIdf
- Classifier: XGBoostRegressor
"""

from _typeshed import OpenBinaryMode
import json
import math
import pickle
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

import jiwer
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from tqdm import tqdm
from xgboost import XGBRegressor

from dialogy.base.plugin import Plugin
from dialogy.types import plugin


class FeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.vectorizer = TfidfVectorizer()

    def read_data(self, fname: Any) -> pd.DataFrame:
        if isinstance(fname, pd.DataFrame):
            return fname
        cux = sqlite3.connect(fname)
        return pd.read_sql_query("SELECT * FROM DATA", cux)

    def fit(self, filename: str, y=None):
        df = self.read_sqlite(filename)
        texts = []
        for _, row in tqdm(df.iterrows()):
            real_transcript = json.loads(row["tag"])["text"]
            texts.append(real_transcript)
            alts = json.loads(row["data"])["alternatives"]
            if alts in [[], [None]]:
                continue
            for alt in alts[0]:
                texts.append(alt["transcript"])

        self.vectorizer.fit(texts)
        return self

    def features(self, alt: Dict) -> List:
        l = len(alt["transcript"].split())
        return self.vectorizer.transform([alt["transcript"]]).todense().tolist()[0] + [
            alt["am_score"] / l,
            alt["lm_score"] / l,
            alt["transcript"].count("UNK"),
            l,
            alt["am_score"] / math.log(1 + l),
            alt["lm_score"] / math.log(1 + l),
            alt["am_score"] / math.sqrt(l),
            alt["am_score"] / math.sqrt(l),
        ]

    def transform(self, filename: str) -> Tuple[np.ndarray, List]:
        df = self.read_sqlite(filename)
        features, targets = [], []
        print(df.head())
        for _, row in tqdm(df.iterrows()):
            real_transcript = json.loads(row["tag"])["text"]
            alts = json.loads(row["data"])["alternatives"]
            if alts in [[], [None]]:
                continue
            for alt in alts[0]:
                if any(
                    key not in alt for key in ["am_score", "lm_score", "transcript"]
                ):
                    continue
                features.append(self.features(alt))
                targets.append(jiwer.wer(real_transcript, alt["transcript"]))

        return np.array(features), targets


class CalibrationModel(Plugin):
    def __init__(self) -> None:
        self.extraction_pipeline = FeatureExtractor()
        self.clf = XGBRegressor(n_jobs=4)

    def train(self, filename: str, model_name: str) -> None:
        X, y = self.extraction_pipeline.fit_transform(filename)
        self.clf.fit(X, y)
        self.save(model_name)

    def inference(self, alternatives: List[Dict]) -> np.ndarray:
        return self.clf.predict(self.extraction_pipeline.features(alternatives))

    def save(self, fname: str) -> None:
        pickle.dump(self, open(fname, "wb"))

    def utility(self, *args: Any) -> Any:
        return self.inference(*args)  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    c = CalibrationModel()
    c.train("94.sqlite", "calmodel.pkl")
