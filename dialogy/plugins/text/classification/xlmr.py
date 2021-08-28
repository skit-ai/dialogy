"""
.. _xlmr_classifier:

This module provides a trainable XLMR classifier.
[read-more](https://arxiv.org/abs/1911.02116)
"""
import importlib
import os
import pickle
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd  # type: ignore
from sklearn import preprocessing  # type: ignore

import dialogy.constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.types import Intent
from dialogy.utils import load_file, logger, save_file


class XLMRMultiClass(Plugin):
    """
    This plugin provides a classifier based on `XLM-Roberta <https://arxiv.org/abs/1911.02116>`. 
    """
    def __init__(
        self,
        model_dir: str,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        debug: bool = False,
        threshold: float = 0.1,
        score_round_off: int = 5,
        args: Optional[Dict[str, Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            classifer = getattr(
                importlib.import_module(const.XLMR_MODULE), const.XLMR_MULTI_CLASS_MODEL
            )
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError(
                "Plugin requires simpletransformers -- https://simpletransformers.ai/docs/installation/"
            ) from error

        super().__init__(access, mutate, debug=debug)
        self.labelencoder = preprocessing.LabelEncoder()
        self.classifier = classifer
        self.model: Any = None
        self.model_dir = model_dir
        self.fallback_label = "_error_"
        self.data_column = "data"
        self.label_column = "labels"
        self.labelencoder_file_path = os.path.join(self.model_dir, "labelencoder.pkl")
        self.threshold = threshold
        self.round = score_round_off
        self.args = args
        self.kwargs = kwargs or {}
        try:
            if os.path.exists(self.labelencoder_file_path):
                self.init_model()
        except EOFError:
            logger.error(
                f"Plugin {self.__class__.__name__} Failed to load labelencoder from {self.labelencoder_file_path}."
            )

    def init_model(self, n: Optional[int] = None) -> None:
        """
        Initialize the model if artifacts are available.

        :param n: number of labels to train on or predict, defaults to None
        :type n: Optional[int], optional
        :raises ValueError: In case n is not provided or can't be calculated.
        """
        model_dir = const.XLMR_MODEL_TIER
        if os.path.exists(self.labelencoder_file_path):
            self.load()
            n = len(self.labelencoder.classes_)
            model_dir = self.model_dir
        if not n:
            raise ValueError(
                f"Plugin {self.__class__.__name__} needs either the training data or an existing labelencoder to initialize."
            )
        try:
            self.model = self.classifier(
                const.XLMR_MODEL,
                model_dir,
                num_labels=n,
                args=self.args,
                **self.kwargs,
            )
        except OSError:
            self.model = self.classifier(
                const.XLMR_MODEL,
                const.XLMR_MODEL_TIER,
                num_labels=n,
                args=self.args,
                **self.kwargs,
            )

    @property
    def valid_labelencoder(self) -> bool:
        return hasattr(self.labelencoder, "classes_")

    def inference(self, texts: List[str]) -> List[Intent]:
        """
        Predict the intent of a list of texts.

        :param texts: A list of strings, derived from ASR transcripts.
        :type texts: List[str]
        :raises AttributeError: In case the labelencoder is not available.
        :return: A list of intents corresponding to texts.
        :rtype: List[Intent]
        """
        fallback_output = Intent(name=self.fallback_label, score=1.0).add_parser(self.__class__)
        if self.model is None:
            return [fallback_output]

        if not self.valid_labelencoder:
            raise AttributeError(
                f"Seems like you forgot to save the {self.__class__.__name__} plugin."
            )

        predictions, logits = self.model.predict(texts)
        if not predictions:
            return [fallback_output]

        confidence_list = [max(np.exp(logit) / sum(np.exp(logit))) for logit in logits]
        predicted_intents = self.labelencoder.inverse_transform(predictions)

        return [
            Intent(name=intent, score=round(score, self.round)).add_parser(
                self.__class__
            ) if score > self.threshold else fallback_output
            for intent, score in zip(predicted_intents, confidence_list)
        ]

    def validate(self, training_data: pd.DataFrame) -> bool:
        """
        Validate the training data is in the appropriate format

        :param training_data: A pandas dataframe containing at least list of strings and corresponding labels.
        :type training_data: pd.DataFrame
        :return: True if the dataframe is valid, False otherwise.
        :rtype: bool
        """
        if training_data.empty:
            logger.error("Training dataframe is empty.")
            return False

        for column in [self.data_column, self.label_column]:
            if column not in training_data.columns:
                logger.error(f"Column {column} not found in training data")
                return False
        return True

    def train(self, training_data: pd.DataFrame) -> None:
        """
        Train an intent-classifier on the provided training data.

        :param training_data: A pandas dataframe containing at least list of strings and corresponding labels.
        :type training_data: pd.DataFrame
        :raises ValueError: In case the training data is not valid.
        """
        if not self.validate(training_data):
            raise ValueError("Training dataframe is invalid.")
        encoder = self.labelencoder.fit(training_data[self.label_column])
        training_data.rename(columns={self.data_column: "text"}, inplace=True)
        training_data[self.label_column] = encoder.transform(
            training_data[self.label_column]
        )
        self.init_model(len(encoder.classes_))
        self.model.train_model(training_data)
        self.save()

    def save(self) -> None:
        """
        Save the plugin artifacts.

        :raises ValueError: In case the labelencoder is not trained.
        """
        if not self.model or not self.valid_labelencoder:
            raise ValueError(
                f"Plugin {self.__class__.__name__} seems to be un-trained."
            )
        save_file(
            self.labelencoder_file_path,
            self.labelencoder,
            mode="wb",
            writer=pickle.dump,
        )

    def load(self) -> None:
        """
        Load the plugin artifacts.
        """
        self.labelencoder = load_file(
            self.labelencoder_file_path, mode="rb", loader=pickle.load
        )

    def utility(self, *args: Any) -> Any:
        return self.inference(*args)
