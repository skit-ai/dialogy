"""
.. _xlmr_classifier:

This module provides a trainable XLMR classifier.
[read-more](https://arxiv.org/abs/1911.02116)
"""
import importlib
import os
import pickle
import random
import requests
from typing import Any, Dict, List, Optional, Tuple
from pprint import pformat

import numpy as np
import pandas as pd
from sklearn import preprocessing
from tqdm import tqdm

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import Intent
from dialogy.utils import load_file, logger, read_from_json, save_file
from torch.profiler import profile, record_function, ProfilerActivity


class XLMRMultiClass(Plugin):
    """
    This plugin provides a classifier based on `XLM-Roberta <https://arxiv.org/abs/1911.02116>`.

    .. _XLMRMultiClass:
    The use_state flag in the XLMRMultiClass plugin is used to enable the use of state variable as the part of the text input.
    """

    def __init__(
        self,
        dest: Optional[str] = None,
        timeout: float = 0.5,
        url: str = "http://0.0.0.0:8000/",
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
        threshold: float = 0.1,
        score_round_off: int = 5,
        fallback_label: str = const.ERROR_LABEL,
        use_state: bool = False,
        data_column: str = const.DATA,
        label_column: str = const.LABELS,
        state_column: str = const.STATE,
        lang_column: str = const.LANG,
        nls_label_column: str = const.NLS_LABEL,
        prompts_map: Dict[Any, Any] = {const.LANG: []},
        use_prompt: bool = False,
        null_prompt_token: str = const.NULL_PROMPT_TOKEN,
        **kwargs: Any,
    ) -> None:
        super().__init__(dest=dest, guards=guards, debug=debug)
        self.fallback_label = fallback_label
        self.data_column = data_column
        self.label_column = label_column
        self.state_column = state_column
        self.lang_column = lang_column
        self.nls_label_column = nls_label_column
        self.use_state = use_state
        self.use_prompt = use_prompt
        self.null_prompt_token = null_prompt_token
        self.prompts_map = prompts_map

        self.purpose = kwargs.pop("purpose", const.PRODUCTION)

        self.threshold = threshold
        self.round = score_round_off


        self.debug = debug

        # model inference service session configuration
        self.url = url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.mount(
            "http://",
            requests.adapters.HTTPAdapter(
                max_retries=1, pool_maxsize=10, pool_block=True
            ),
        )
        self.headers: Dict[str, str] = {
            "Content-Type": "application/json"
        }

    def _request_model_inference(self, texts: List[str]) -> Tuple[List, List]:
        payload = {
            "transcripts": texts
        }
        try:
            response = self.session.post(
                self.url, json=payload, headers=self.headers, timeout=self.timeout
            )

            if response.status_code == 200:
                # The API call was successful, expect the following to contain entities.
                # A list of dicts or an empty list.
                result = response.json()
                return result.get("intents", {})
            
        except requests.exceptions.Timeout as timeout_exception:
            logger.error(f"Model Inference Service timed out: {timeout_exception}")  # pragma: no cover
            logger.error(pformat(payload))  # pragma: no cover
            return {}  # pragma: no cover
        
        except requests.exceptions.ConnectionError as connection_error:
            logger.error(f"Model Inference Service is turned off?: {connection_error}")
            logger.error(pformat(payload))
            raise requests.exceptions.ConnectionError from connection_error

        # Control flow reaching here would mean the API call wasn't successful.
        # To prevent rest of the things from crashing, we will raise an exception.
        raise ValueError(
            f"Model Inference Service API call failed | [{response.status_code}]: {response.text}"
        )

    def inference(
        self,
        texts: Optional[List[str]],
        state: Optional[str] = None,
        lang: Optional[str] = None,
        nls_label: Optional[str] = None,
    ) -> List[Intent]:

        """
        Predict the intent of a list of texts.
        If the model has been trained using the state features, it expects the text to also be appended with the state token else the predictions would be spurious.

        :param texts: A list of strings, derived from ASR transcripts.
        :param state: state, mapped to the ASR transcripts.
        :type texts: List[str]
        :type state: List[str]
        :raises AttributeError: In case the labelencoder is not available.
        :return: A list of intents corresponding to texts.
        :rtype: List[Intent]
        """

        fallback_output = Intent(name=self.fallback_label, score=1.0).add_parser(self)

        if not texts:
            logger.error(f"texts passed to model {texts}!")
            return [fallback_output]

        if self.use_state and not state:
            raise ValueError(
                f"Plugin {self.__class__.__name__} requires state to be passed to the model."
            )

        if self.use_prompt and not nls_label:
            raise ValueError(
                f"In order to use prompts as feature, Plugin {self.__class__.__name__} is requires the NLS Label to be passed to the model."
            )

        if self.use_prompt and not lang:
            raise ValueError(
                f"In order to use prompts as feature, Plugin {self.__class__.__name__} is requires lang to be passed to the model."
            )

        if self.use_prompt and nls_label:
            texts[0] += "<s> " + self.lookup_prompt(lang, nls_label) + " </s>"

        if self.use_state and state:
            texts[0] += "<s> " + state + " </s>"

        logger.debug(f"Classifier Input:\n{texts}")

        intents = self._request_model_inference(texts)

        return [
            Intent(name=intent, score=round(score, self.round)).add_parser(self)
            for intent, score in intents.items()
        ]

    def validate(self, training_data: pd.DataFrame) -> bool:
        """
        Validate the training data is in the appropriate format

        :param training_data: A pandas dataframe containing at least list of strings and corresponding labels.
            Should also contain a state key if use_state = True while initializing object.
        :type training_data: pd.DataFrame
        :return: True if the dataframe is valid, False otherwise.
        :rtype: bool
        """
        if training_data.empty:
            logger.error("Training dataframe is empty.")
            return False
        expected_columns = [self.data_column, self.label_column]

        if self.use_prompt:
            expected_columns.append(self.lang_column)
            expected_columns.append(self.nls_label_column)

        if self.use_state:
            expected_columns.append(self.state_column)

        for column in expected_columns:
            if column not in training_data.columns:
                logger.warning(f"Column {column} not found in training data")
                return False
        return True

    def lookup_prompt(self, lang: Optional[str], nls_label: Optional[str]) -> str:
        """
        Same as get_prompt() method, but built for faster lookup to reduce latency during inference.
        """
        try:
            return self.prompts_map[lang][nls_label]
        except Exception as e:
            if self.debug:
                logger.debug(e)
                logger.debug(f"Prompt not found for Lang: {lang} \t State: {nls_label}")
            return self.null_prompt_token

    def utility(self, input: Input, _: Output) -> List[Intent]:
        return self.inference(
            input.clf_feature, input.current_state, input.lang, input.nls_label
        )
