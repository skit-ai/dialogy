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
import pandas as pd
from sklearn import preprocessing

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
        use_cuda: bool = False,
        score_round_off: int = 5,
        purpose: str = const.TRAIN,
        fallback_label: str = const.ERROR_LABEL,
        data_column: str = const.DATA,
        label_column: str = const.LABELS,
        args_map: Optional[Dict[str, Any]] = None,
        skip_labels: Optional[List[str]] = None,
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
        self.fallback_label = fallback_label
        self.data_column = data_column
        self.label_column = label_column
        self.use_cuda = use_cuda
        self.labelencoder_file_path = os.path.join(
            self.model_dir, const.LABELENCODER_FILE
        )
        self.threshold = threshold
        self.skip_labels = set(skip_labels or set())
        self.purpose = purpose
        self.round = score_round_off
        if args_map and (
            const.TRAIN not in args_map
            or const.TEST not in args_map
            or const.PRODUCTION not in args_map
        ):
            raise ValueError(
                f"Attempting to set invalid {args_map=}. "
                "It is missing some of {const.TRAIN}, {const.TEST}, {const.PRODUCTION} in configs."
            )
        self.args_map = args_map
        self.kwargs = kwargs or {}
        try:
            if os.path.exists(self.labelencoder_file_path):
                self.init_model()
        except EOFError:
            logger.error(
                f"Plugin {self.__class__.__name__} Failed to load labelencoder from {self.labelencoder_file_path}. "
                "Ignore this message if you are training but if you are using this in production or testing, then this is serious!"
            )

    def init_model(self, label_count: Optional[int] = None) -> None:
        """
        Initialize the model if artifacts are available.

        :param label_count: number of labels to train on or predict, defaults to None
        :type label_count: Optional[int], optional
        :raises ValueError: In case n is not provided or can't be calculated.
        """
        model_dir = const.XLMR_MODEL_TIER
        if os.path.exists(self.labelencoder_file_path):
            self.load()
            label_count = len(self.labelencoder.classes_)
            model_dir = self.model_dir
        if not label_count:
            raise ValueError(
                f"Plugin {self.__class__.__name__} needs either the training data or an existing labelencoder to initialize."
            )
        args = (
            self.args_map[self.purpose]
            if self.args_map and self.purpose in self.args_map
            else {}
        )
        try:
            self.model = self.classifier(
                const.XLMR_MODEL,
                model_dir,
                num_labels=label_count,
                use_cuda=self.use_cuda,
                args=args,
                **self.kwargs,
            )
        except OSError:
            self.model = self.classifier(
                const.XLMR_MODEL,
                const.XLMR_MODEL_TIER,
                num_labels=label_count,
                use_cuda=self.use_cuda,
                args=args,
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
        logger.debug(f"Classifier input:\n{texts}")
        fallback_output = Intent(name=self.fallback_label, score=1.0).add_parser(
            self.__class__
        )

        if self.model is None:
            logger.error(f"No model found for plugin {self.__class__.__name__}!")
            return [fallback_output]

        if not self.valid_labelencoder:
            raise AttributeError(
                "Seems like you forgot to "
                f"save the {self.__class__.__name__} plugin."
            )

        if not texts:
            return [fallback_output]

        predictions, logits = self.model.predict(texts)
        if not predictions:
            return [fallback_output]

        confidence_list = [max(np.exp(logit) / sum(np.exp(logit))) for logit in logits]
        predicted_intents = self.labelencoder.inverse_transform(predictions)

        return [
            Intent(name=intent, score=round(score, self.round)).add_parser(
                self.__class__
            )
            if score > self.threshold
            else fallback_output
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
                logger.warning(f"Column {column} not found in training data")
                return False
        return True

    def train(self, training_data: pd.DataFrame) -> None:
        """
        Train an intent-classifier on the provided training data.

        The training is skipped if the data-format is not valid.
        :param training_data: A pandas dataframe containing at least list of strings and corresponding labels.
        :type training_data: pd.DataFrame
        """
        if not self.validate(training_data):
            logger.warning(
                f"Training dataframe is invalid, for {self.__class__.__name__} plugin."
            )
            return

        skip_labels_filter = training_data[self.label_column].isin(self.skip_labels)
        training_data = training_data[~skip_labels_filter].copy()

        encoder = self.labelencoder.fit(training_data[self.label_column])
        sample_size = 5 if len(training_data) > 5 else len(training_data)
        training_data.rename(
            columns={self.data_column: const.TEXT, self.label_column: const.LABELS},
            inplace=True,
        )
        training_data.loc[:, const.LABELS] = encoder.transform(
            training_data[const.LABELS]
        )
        training_data = training_data[[const.TEXT, const.LABELS]]
        self.init_model(len(encoder.classes_))
        logger.debug(
            f"Displaying a few samples (this goes into the model):\n{training_data.sample(sample_size)}\nLabels: {len(encoder.classes_)}."
        )
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
        return self.inference(*args)  # pylint: disable=no-value-for-parameter
