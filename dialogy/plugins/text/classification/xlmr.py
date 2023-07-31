"""
.. _xlmr_classifier:

This module provides a trainable XLMR classifier.
[read-more](https://arxiv.org/abs/1911.02116)
"""
import importlib
import os
import pickle
import requests
from typing import Any, Dict, List, Optional, Tuple
from pprint import pformat

import numpy as np
import pandas as pd
from sklearn import preprocessing
from tqdm import tqdm
import aiohttp
import json
from aiohttp.client_exceptions import ClientConnectorError

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import Intent
from dialogy.utils import load_file, logger, read_from_json, save_file
import torch
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
        args_map: Optional[Dict[str, Any]] = None,
        skip_labels: Optional[List[str]] = None,
        prompts_map: Dict[Any, Any] = {const.LANG: []},
        use_prompt: bool = False,
        null_prompt_token: str = const.NULL_PROMPT_TOKEN,
        **kwargs: Any,
    ) -> None:
        super().__init__(dest=dest, guards=guards, debug=debug, **kwargs)
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
        self.skip_labels = set(skip_labels or set())
        self.threshold = threshold
        self.round = score_round_off

        if not args_map and self.purpose != const.PRODUCTION:
            raise ValueError(
                f"args_map was set to None with purpose={self.purpose} which is not allowed."
            )
        if args_map and self.purpose not in args_map:
            raise ValueError(
                f"Attempting to set invalid `args_map`. "
                f"It is missing {self.purpose}. `purpose` has to be one of "
                f"{const.TRAIN}, {const.TEST}, {const.PRODUCTION} in configs."
            )
        if args_map:
            self.args_map = args_map[self.purpose]
        else:
            self.args_map = {}

        self.use_calibration = self.args_map.get(const.MODEL_CALIBRATION, False)

        self.model_dir = self.args_map.get("best_model_dir")

        if self.model_dir:
            self.ts_parameter: float = read_from_json([const.TS_PARAMETER], self.model_dir,
                                                      const.CALIBRATION_CONFIG_FILE).get(
                const.TS_PARAMETER) or self.args_map.get(const.TS_PARAMETER) or 1.0

        # flag that specifies whether plugin is being imported externally solely for model
        imported = kwargs.get("imported", False)

        if self.purpose in [const.TRAIN, const.TEST] or imported:
            self.use_cuda = torch.cuda.is_available()
            try:
                classifer = getattr(
                    importlib.import_module(const.XLMR_MODULE), const.XLMR_MULTI_CLASS_MODEL
                )
            except ModuleNotFoundError as error:
                raise ModuleNotFoundError(
                    "Plugin requires simpletransformers -- https://simpletransformers.ai/docs/installation/"
                ) from error

            if not self.model_dir:
                raise ValueError(
                    f"'best_model_dir' missing in passed args_map."
                )

            self.labelencoder = preprocessing.LabelEncoder()
            self.classifier = classifer
            self.model: Any = None

            self.labelencoder_file_path = os.path.join(
                self.model_dir, const.LABELENCODER_FILE
            )

            self.kwargs = kwargs or {}

            # TODO: check if this can be avoided
            avoiding_keys = ["name", "imported", "purpose", "project_name"]
            for key in avoiding_keys:
                if key in self.kwargs:
                    del self.kwargs[key]

            try:
                if os.path.exists(self.labelencoder_file_path):
                    logger.debug(f"initializing label encoder file from {self.labelencoder_file_path}")
                    self.init_model()
            except EOFError:
                logger.error(
                    f"Plugin {self} Failed to load labelencoder from {self.labelencoder_file_path}. "
                    "Ignore this message if you are training but if you are using this in "
                    "production or testing, then this should be checked!"
                )

        elif self.purpose == const.PRODUCTION:
            # model inference service session configuration
            self.url = url
            self.timeout = timeout
            self.headers: Dict[str, str] = {
                "Content-Type": "application/json"
            }

        self.debug = debug

    def init_model(self, label_count: Optional[int] = None) -> None:
        """
        Initialize the model if artifacts are available.
        :param label_count: number of labels to train on or predict, defaults to None
        :type label_count: Optional[int], optional
        :raises ValueError: In case n is not provided or can't be calculated.
        """
        if os.path.exists(self.labelencoder_file_path):
            self.load()
            label_count = len(self.labelencoder.classes_)
        if not label_count:
            raise ValueError(
                f"Plugin {self} needs either the training data "
                "or an existing labelencoder to initialize."
            )

        try:
            logger.debug(f"loading model weights from {self.model_dir}")
            self.model = self.classifier(
                const.XLMR_MODEL,
                self.model_dir,
                num_labels=label_count,
                use_cuda=self.use_cuda,
                args=self.args_map,
                **self.kwargs,
            )
        except OSError:
            logger.info(f"Model not found at {self.model_dir}. "
                        f"Default model weights will be loaded")
            self.model = self.classifier(
                const.XLMR_MODEL,
                const.XLMR_MODEL_TIER,
                num_labels=label_count,
                use_cuda=self.use_cuda,
                args=self.args_map,
                **self.kwargs,
            )

    @property
    def valid_labelencoder(self) -> bool:
        return hasattr(self.labelencoder, "classes_")

    async def _request_model_inference(self, texts: List[str]) -> Tuple[Any, Any]:
        payload = {"transcripts": texts}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, data=json.dumps(payload), headers=self.headers) as resp:
                    status_code = resp.status
                    if status_code == 200:
                        result = await resp.json()
                        return result.get("intents", []), result.get("logits", [])
                    else:
                        result = await resp.text()
        except ClientConnectorError as connection_error:
            logger.error(f"Model Inference Service is turned off?: {connection_error}")
            logger.error(pformat(payload))
            raise requests.exceptions.ConnectionError from connection_error

        # Control flow reaching here would mean the API call wasn't successful.
        # To prevent rest of the things from crashing, we will raise an exception.
        raise ValueError(
            f"Model Inference Service API call failed | [{status_code}]: {result}"
        )

    async def inference(
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

        # validation
        fallback_output = Intent(name=self.fallback_label, score=1.0).add_parser(self)
        if not texts:
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

        # preprocessing
        if self.use_prompt and nls_label:
            texts[0] += "<s> " + self.lookup_prompt(lang, nls_label) + " </s>"

        if self.use_state and state:
            texts[0] += "<s> " + state + " </s>"

        logger.debug(f"Classifier Input:\n{texts}")

        # inference
        if self.purpose == const.PRODUCTION:
            predicted_intents, logits = await self._request_model_inference(texts)
            # postprocessing
            logits = np.array(logits)

        elif self.purpose == const.TEST:
            if not self.model:
                return [fallback_output]
            predictions, logits = self.model.predict(texts)
            if not predictions:
                return [fallback_output]

        else:
            raise RuntimeError(f"Inference method called with purpose "
                               f"set to '{self.purpose}'. Valid "
                               f"values - [{const.PRODUCTION}, {const.TEST}]")

        logits = logits / self.ts_parameter
        confidence_scores = [np.exp(logit) / sum(np.exp(logit)) for logit in logits]
        intents_confidence_order = np.argsort(confidence_scores)[0][::-1]

        ordered_confidence_scores = [
            confidence_scores[0][idx] for idx in intents_confidence_order
        ]

        if self.purpose == const.TEST:
            predicted_intents = self.labelencoder.inverse_transform(
                intents_confidence_order
            )

        if self.use_calibration:
            ordered_confidence_scores = [
                logits[0][idx] for idx in np.argsort(logits)[0][::-1]
            ]  # ordered logits for calibration

        return [
            Intent(name=intent, score=round(score, self.round)).add_parser(self)
            for intent, score in zip(predicted_intents, ordered_confidence_scores)
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
    
    def train(self, training_data: pd.DataFrame) -> None:
        """
        Train an intent-classifier on the provided training data.
        The training is skipped if the data-format is not valid.
        While training with the use_state flag as true, make sure that the state column is the part of the training_data dataframe
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

        # Append state to text
        if self.use_state:
            training_data[const.TEXT] += (
                "<s> " + training_data[self.state_column] + " </s>"
            )

        # Append prompt to text
        if self.use_prompt:
            logger.debug("Adding prompts to input text")
            for i in tqdm(range(training_data.shape[0]), desc="progress bar:"):
                _lang = training_data.iloc[i][self.lang_column]
                _nls_label = training_data.iloc[i][self.nls_label_column]
                _prompt = self.lookup_prompt(_lang, _nls_label)
                training_data.at[i, const.TEXT] = (
                    training_data.iloc[i][const.TEXT] + "<s> " + _prompt
                    if _prompt
                    else self.null_prompt_token + " </s>"
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
        
    def load(self) -> None:
        """
        Load the plugin artifacts.
        """
        self.labelencoder = load_file(
            self.labelencoder_file_path, mode="rb", loader=pickle.load
        )

    async def utility(self, input: Input, _: Output) -> List[Intent]:
        return await self.inference(
            input.clf_feature, input.current_state, input.lang, input.nls_label
        )
