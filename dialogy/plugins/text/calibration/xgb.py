"""
Trains a calibraation model. This contains two models:
- Vectorizer: TfIdf
- Classifier: XGBoostRegressor
"""

import json
import math
import pickle
import traceback
from typing import Any, Dict, List, Optional, Tuple

import jiwer
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from tqdm import tqdm
from xgboost import XGBRegressor

from dialogy import constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.types import Transcript, Utterance
from dialogy.utils import logger, normalize


class FeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self) -> None:
        super().__init__()
        self.vectorizer = TfidfVectorizer()

    def fit(self, df: pd.DataFrame, y: Any = None) -> Any:
        texts = []
        for _, row in tqdm(df.iterrows()):
            real_transcript = json.loads(row["tag"])["text"]
            texts.append(real_transcript)
            alts = json.loads(row["data"])["alternatives"]
            if alts not in [[], [None]]:
                for alt in alts[0]:
                    texts.append(alt["transcript"])

        logger.debug("Step 1/2: Training vectorizer model")
        self.vectorizer.fit(texts)
        return self

    def features(self, alternatives: List[Dict[str, Any]]) -> List[List[float]]:
        features = []
        for alt in alternatives:
            try:
                l = len(alt["transcript"].split())
                features.append(
                    self.vectorizer.transform([alt["transcript"]]).todense().tolist()[0]
                    + [
                        alt["am_score"] / l,
                        alt["lm_score"] / l,
                        alt["transcript"].count("UNK"),
                        l,
                        alt["am_score"] / math.log(1 + l),
                        alt["lm_score"] / math.log(1 + l),
                        alt["am_score"] / math.sqrt(l),
                        alt["am_score"] / math.sqrt(l),
                    ]
                )
            except Exception as error:
                logger.error(f"{error}\n{traceback.format_exc()}")

        return features

    def transform(self, df: pd.DataFrame) -> Tuple[Any, Any]:
        features, targets = [], []
        for _, row in tqdm(df.iterrows()):
            real_transcript = json.loads(row["tag"])["text"]
            alts = json.loads(row["data"])["alternatives"][0]
            if alts not in [[], [None]]:
                features.append(self.features(alts))
                targets += [
                    jiwer.wer(real_transcript, alt["transcript"]) for alt in alts
                ]
        return np.squeeze(np.array(features)), targets


class CalibrationModel(Plugin):
    """
    This plugin provides a calibration model that sits between ASR and SLU.
    It trains a model that learn to classify alternatives from the text and
    AM, LM score. Bad alternatives are removed before training SLU and during
    inference.
    """

    def __init__(
        self,
        access: Optional[PluginFn],
        mutate: Optional[PluginFn],
        threshold: float,
        debug: bool = False,
    ) -> None:
        super().__init__(access, mutate, debug=debug)
        self.extraction_pipeline = FeatureExtractor()
        self.clf = XGBRegressor(n_jobs=1)
        self.data_column = "data"
        self.threshold = threshold  # Todo : make configurable

    def train(self, df: pd.DataFrame, model_name: str = "calibration.pkl") -> None:
        """
        Trains the calibration pipeline.

        :param df: dataframe to train on. Should be a valid transcrition tagging job.
        :param model_name: Saves the pipline as {model_name}.pkl
        :type df: pd.DataFrame
        :type model_name: str
        """
        X, y = self.extraction_pipeline.fit_transform(df)
        logger.debug("Step 2/2: Training regressor model")
        self.clf.fit(X, y)
        self.save(model_name)

    def predict(self, alternatives: List[Dict[str, Any]]) -> Any:
        return self.clf.predict(
            np.array(self.extraction_pipeline.features(alternatives))
        )

    def filter_asr_output(self, asr_output: Dict[str, Any]) -> List[Any]:
        """
        Filters outputs from ASR based on calibration model prediction.

        :param asr_output: output dictionary from ASR. Should have an _alternatives_
                            key.
        :type asr_output: Dict[str, Any]
        :return: Filtered alternatives, in the same format as input.
        :rtype: Dict[str, Any]
        """
        alternatives = asr_output["alternatives"][0]
        filtered_alternatives = []
        prediction = self.predict(alternatives)
        for alternative, wer in zip(alternatives, prediction):
            if wer < self.threshold:
                filtered_alternatives.append(alternative)
        return filtered_alternatives

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
                    filtered_asr_output = {
                        "alternatives": self.filter_asr_output(asr_output)
                    }
                    training_data.iloc[i][self.data_column] = filtered_asr_output
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

    def inference(self, utterances: List[Utterance]) -> List[str]:
        transcripts: List[Transcript] = normalize(utterances)
        transcript_lengths: List[int] = [
            len(transcript.split()) for transcript in transcripts
        ]
        average_word_count: float = (
            sum(transcript_lengths) / len(transcript_lengths) if transcripts else 0.0
        )

        # We want to run this plugin if transcripts have more than WORD_THRESHOLD words
        # below that count, WER is mostly high. We expect this plugin to override
        # a classifier's prediction to a fallback label.
        # If the transcripts have less than WORD_THRESHOLD words, we will always predict the fallback label.
        if average_word_count <= const.WORD_THRESHOLD:
            return normalize(utterances)

        return normalize(
            [
                self.filter_asr_output({"alternatives": [utterance]})
                for utterance in utterances
            ]
        )

    def save(self, fname: str) -> None:
        pickle.dump(self, open(fname, "wb"))

    def utility(self, *args: Any) -> Any:
        return self.inference(*args)  # pylint: disable=no-value-for-parameter

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Return if `df` is a valid trascription tagging job
        should return `False` for intent tagging jobs.
        example : ` '{"text": "I want to change and set my <INAUDIBLE>", "type": "TRANSCRIPT"}'`

        Sharp bits:
        - All rows in df should have same format. We just consider
         the first row for sanity checks.

        :param df: Input dataframe.
        :type df: pd.DataFrame

        :return: (bool) if the dataframe is valid for training calibration model.
        :rtype: bool
        """
        required_keys = ["text", "type"]
        tagged_data = json.loads(df.iloc[0]["tag"])
        if all(key in tagged_data for key in required_keys):
            if tagged_data["type"] == "TRANSCRIPT":
                return True
        return False