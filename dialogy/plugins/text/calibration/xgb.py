"""
Trains a calibraation model. This contains two models:
- Vectorizer: TfIdf
- Classifier: XGBoostRegressor
"""

import json
import math
import pickle
import sqlite3
import traceback
from typing import Any, Dict, List, Optional, Tuple

from pandas.core.frame import DataFrame
from dialogy.utils import logger
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

    def fit(self, df: pd.DataFrame, y=None):
        texts = []
        for _, row in tqdm(df.iterrows()):
            real_transcript = json.loads(row["tag"])["text"]
            texts.append(real_transcript)
            alts = json.loads(row["data"])["alternatives"]
            if alts in [[], [None]]:
                continue
            for alt in alts[0]:
                texts.append(alt["transcript"])

        logger.debug("Step 1/2: Training vectorizer model")
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

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, List]:
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
    def __init__(self, threshold) -> None:
        self.extraction_pipeline = FeatureExtractor()
        self.clf = XGBRegressor(n_jobs=4)
        self.data_column = "data"
        self.threshold = threshold  # Todo : make configurable

    def train(self, filename: str, model_name: str) -> None:
        X, y = self.extraction_pipeline.fit_transform(filename)
        logger.debug("Step 2/2: Training regressor model")
        self.clf.fit(X, y)
        self.save(model_name)

    def filter_asr_output(self, asr_output: dict) -> dict:
        alternatives = asr_output["alternatives"]
        filtered_alternatives = []
        for alternative in alternatives[0]:
            if self.inference(alternative) < self.threshold:
                filtered_alternatives.append(alternative)
        return {"alternatives": [filtered_alternatives]}

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        # filters df alternatives and feeds into merge_asr_output,
        # doesn't change training_data schema
        training_data["use"] = True
        logger.debug("Transforming training data.")
        for i, row in training_data.iterrows():
            asr_output = None
            try:
                asr_output = json.loads(row[self.data_column])
                if asr_output:
                    filtered_asr_output = self.filter_asr_output(asr_output)
                    training_data.loc[i, self.data_column] = filtered_asr_output
                else:
                    training_data.loc[i, "use"] = False
            except Exception as error:  # pylint: disable=broad-except
                training_data.loc[i, "use"] = False
                logger.error(f"{error} -- {asr_output}\n{traceback.format_exc()}")

        training_data_ = training_data[training_data.use].copy()
        training_data_.drop("use", axis=1, inplace=True)
        discarded_data = len(training_data) - len(training_data_)
        if discarded_data:
            logger.debug(
                f"Discarding {discarded_data} samples because the alternatives couldn't be parsed."
            )
        return training_data_

    def inference(self, alternatives: List[Dict]) -> np.ndarray:
        return self.clf.predict(self.extraction_pipeline.features(alternatives))

    def save(self, fname: str) -> None:
        pickle.dump(self, open(fname, "wb"))

    def utility(self, *args: Any) -> Any:
        return self.inference(*args)  # pylint: disable=no-value-for-parameter
