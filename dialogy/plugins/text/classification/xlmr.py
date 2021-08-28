"""
This module provides a trainable XLMR classifier.
[read-more](https://arxiv.org/abs/1911.02116)
"""
import importlib
from typing import Any, List, Optional

import numpy as np
import pandas as pd  # type: ignore
from sklearn import preprocessing  # type: ignore

import dialogy.constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.types import Intent
from dialogy.utils.logger import log


class XLMRMultiClass(Plugin):
    """"""

    def __init__(
        self, access: Optional[PluginFn], mutate: Optional[PluginFn], debug: bool
    ) -> None:
        try:
            model = getattr(
                importlib.import_module(const.XLMR_MODULE), const.XLMR_MULTI_CLASS_MODEL
            )
        except ModuleNotFoundError as error:
            raise ModuleNotFoundError(
                "Plugin requires simpletransformers -- https://simpletransformers.ai/docs/installation/"
            ) from error

        self.labelencoder = preprocessing.LabelEncoder()
        super().__init__(access, mutate, debug=debug)
        self.model = model
        self.fallback_label = "_error_"
        self.training_data_schema = {"text": str, "labels": int}

    def inference(self, texts: List[str]) -> List[Intent]:
        fallback_output = [Intent(name=self.fallback_label, score=1.0)]
        if self.model is None:
            return fallback_output

        if not hasattr(self.labelencoder, "classes_"):
            raise AttributeError(
                f"Seems like you forgot to save the {self.__class__.__name__} plugin."
            )

        predictions, logits = self.model.predict(texts)
        if not predictions:
            return fallback_output

        confidence_list = [max(np.exp(logit) / sum(np.exp(logit))) for logit in logits]
        predicted_intents = self.labelencoder.inverse_transform(predictions)

        return [
            Intent(name=intent, score=score).add_parser(self.__class__)
            for intent, score in zip(predicted_intents, confidence_list)
        ]

    def validate(self, training_data: pd.DataFrame) -> bool:
        if not training_data.empty:
            log.error("Training dataframe is empty.")
            return False

        for column, dtype in self.training_data_schema.items():
            if column not in training_data.columns:
                log.error(f"Column {column} not found in training data")
                return False

        columns = list(self.training_data_schema.keys())

        for _, row in training_data[columns].iterrows():
            for column in columns:
                dtype = self.training_data_schema[column]
                if not isinstance(row[column], dtype):
                    log.error(f"Column {type(column)=} but expected {dtype}")
                    return False

    def train(self, training_data: pd.DataFrame) -> None:
        self.validate(training_data)

        if not hasattr(self.labelencoder, "classes_"):
            self.labelencoder.fit(training_data)

        labels = self.labelencoder.transform(training_data)
        self.model.fit(training_data, labels)

    def utility(self, *args: Any) -> Any:
        return self.inference(*args)
