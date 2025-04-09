"""
.. _xlmr_classifier:

This module provides a trainable XLMR classifier.
[read-more](https://arxiv.org/abs/1911.02116)
"""
import importlib
import os
import shutil
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
from dialogy.utils import load_file, logger, read_from_json, save_file, remove_directory
import torch
from torch.profiler import profile, record_function, ProfilerActivity
from sklearn.model_selection import train_test_split
import logging
import shutil
import matplotlib.pyplot as plt
from sklearn.metrics import f1_score

logging.basicConfig(level=logging.INFO)


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
                training_args = getattr(
                    importlib.import_module(const.XLMR_MODULE), const.XLMR_TRAINING_ARGS
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
            self.trainingArgs = training_args()

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
                    self.init_model(self.args_map)
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

    def init_model(self, args,label_count: Optional[int] = None) -> None:
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
                args=self.trainingArgs,
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
                args=self.trainingArgs,
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
        try:
            eval_data_path = self.args_map.get(const.EVAL_DATA_DIR)
            eval_data = pd.read_csv(os.path.join(eval_data_path, const.TEST)+'.csv')
        except (FileNotFoundError, pd.errors.ParserError) as e:
            logger.exception(f"Error loading Eval Data: {e}")
            return
        
        logger.info(f"\n\nTrain shape: {training_data.shape}\tTest shape: {eval_data.shape}\n\n")
        
        if not self.validate(eval_data):
            logger.warning(
                f"Evaluation dataframe is invalid, for {self.__class__.__name__} plugin."
            )
            return

        train_skip_labels_filter = training_data[self.label_column].isin(self.skip_labels)
        training_data = training_data[~train_skip_labels_filter].copy()
        eval_skip_labels_filter = eval_data[self.label_column].isin(self.skip_labels)
        eval_data = eval_data[~eval_skip_labels_filter].copy()

        encoder = self.labelencoder.fit(training_data[self.label_column])

        sample_size = 5 if len(training_data) > 5 else len(training_data)
        training_data.rename(
            columns={self.data_column: const.TEXT, self.label_column: const.LABELS},
            inplace=True,
        )
        eval_data.rename(
            columns={self.data_column: const.TEXT, self.label_column: const.LABELS},
            inplace=True,
        )
        training_data.loc[:, const.LABELS] = encoder.transform(
            training_data[const.LABELS]
        )
        eval_data.loc[:, const.LABELS] = encoder.transform(
            eval_data[const.LABELS]
        )

        # Append state to text
        if self.use_state:
            training_data[const.TEXT] += (
                "<s> " + training_data[self.state_column] + " </s>"
            )
            eval_data[const.TEXT] += (
                "<s> " + eval_data[self.state_column] + " </s>"
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
            for i in tqdm(range(eval_data.shape[0]), desc="progress bar:"):
                _lang = eval_data.iloc[i][self.lang_column]
                _nls_label = eval_data.iloc[i][self.nls_label_column]
                _prompt = self.lookup_prompt(_lang, _nls_label)
                eval_data.at[i, const.TEXT] = (
                    eval_data.iloc[i][const.TEXT] + "<s> " + _prompt
                    if _prompt
                    else self.null_prompt_token + " </s>"
                )

        training_data = training_data[[const.TEXT, const.LABELS]]
        eval_data = eval_data[[const.TEXT, const.LABELS]]

        logger.debug(
            f"Displaying a few train samples (this goes into the model):\n{training_data.sample(sample_size)}\nLabels: {len(encoder.classes_)}."
        )
        logger.debug(
            f"Displaying a few eval samples (this goes into the model):\n{eval_data.sample(sample_size)}\nLabels: {len(encoder.classes_)}."
        )

        def weighted_f1(labels, preds):
            return f1_score(labels, preds, average='weighted')

        # Common Training parameters
        self.trainingArgs.num_train_epochs = self.args_map.get(const.NUM_TRAIN_EPOCHS,10)
        self.trainingArgs.overwrite_output_dir = self.args_map.get(const.OVERRIDE_OUTPUT_DIR, True)
        self.trainingArgs.train_batch_size = self.args_map.get(const.TRAIN_BATCH_SIZE, 16)
        self.trainingArgs.use_multiprocessing = self.args_map.get(const.USE_MULTIPROCESSING, False)
        self.trainingArgs.save_model_every_epoch = self.args_map.get(const.SAVE_MODEL_EVERY_EPOCH, False)
        self.trainingArgs.save_best_model = self.args_map.get(const.SAVE_BEST_MODEL, False)
        self.trainingArgs.save_steps = self.args_map.get(const.SAVE_STEPS, -1)  # Added save_steps
        self.trainingArgs.fp16 = self.args_map.get(const.FP16, False)  # Added fp16
        self.trainingArgs.learning_rate = self.args_map.get(const.LEARNING_RATE, 1.0e-05)  # Added learning_rate
        self.trainingArgs.max_seq_length = self.args_map.get(const.MAX_SEQ_LENGTH, 176)  # Added max_seq_length
        self.trainingArgs.reprocess_input_data = self.args_map.get(const.REPROCESS_INPUT_DATA, True)  # Added reprocess_input_data
        self.trainingArgs.evaluate_during_training = self.args_map.get(const.EVALUATE_DURING_TRAINING,True)
        self.trainingArgs.evaluate_during_training_verbose = self.args_map.get(const.EVALUATE_DURING_TRAINING_VERBOSE,True)
        self.trainingArgs.save_eval_checkpoints = self.args_map.get(const.SAVE_EVAL_CHECKPOINTS, False)
        self.trainingArgs.use_multiprocessing_for_evaluation = self.args_map.get(const.USE_MULTIPROCESSING_FOR_EVALUATION, False)
        
        # Metrics where higher values indicate worse performance (should be minimized)
        
        early_stopping_metric = self.args_map.get(const.EARLY_STOPPING_METRIC, "weighted_f1")
        if early_stopping_metric in const.MINIMIZE_METRICS:
            self.trainingArgs.early_stopping_metric_minimize = True
        else:
            self.trainingArgs.early_stopping_metric_minimize = False
        self.trainingArgs.early_stopping_metric = early_stopping_metric
        # Had to rely on this logic beacuse in simple transformers evaluation and best model saving is very interwined with early stopping logic
        self.trainingArgs.output_dir = self.args_map.get(const.BEST_MODEL_DIR, "data/classification/models")
        self.trainingArgs.best_model_dir = self.args_map.get(const.OUTPUT_DIR, "data/classification/temp")

        if self.args_map.get(const.USE_EARLY_STOPPING, True):
            self.trainingArgs.use_early_stopping = self.args_map.get(const.USE_EARLY_STOPPING, True)
            self.trainingArgs.save_optimizer_and_scheduler = self.args_map.get(const.SAVE_OPTIMIZER_AND_SCHEDULER, False) # By default it should be False, else the model size will be too large
            self.trainingArgs.early_stopping_consider_epochs = self.args_map.get(const.EARLY_STOPPING_CONSIDER_EPOCHS,True)
            self.trainingArgs.early_stopping_patience = self.args_map.get(const.EARLY_STOPPING_PATIENCE, 3)
            self.trainingArgs.early_stopping_delta = self.args_map.get(const.EARLY_STOPPING_DELTA, 0.01)  # Changed to False since higher MCC is better
            # Had to rely on this logic beacuse in simple transformers evaluation and best model saving is very interwined with early stopping logic
            self.trainingArgs.best_model_dir = self.args_map.get(const.BEST_MODEL_DIR, "data/classification/models")
            self.trainingArgs.output_dir = self.args_map.get(const.OUTPUT_DIR, "data/classification/temp")

        self.init_model(self.trainingArgs, len(encoder.classes_))
        self.model.train_model(training_data, eval_df=eval_data,  weighted_f1=weighted_f1)
        logger.info(f"Best Model saved to {self.trainingArgs.best_model_dir}")
        
        try:
            # Move training progress file to metrics directory if it exists
            progress_file = os.path.join(self.trainingArgs.output_dir, const.TRAINING_PROGRESS_FILE)
            if os.path.exists(progress_file):
                parent_dir = os.path.dirname(self.trainingArgs.output_dir)
                shutil.move(progress_file, os.path.join(parent_dir, const.METRICS, const.TRAINING_PROGRESS_FILE))
            
            # Remove the training artifacts
            if self.args_map.get(const.USE_EARLY_STOPPING, True) and os.path.exists(self.trainingArgs.output_dir):
                shutil.rmtree(self.trainingArgs.output_dir)
            elif not self.args_map.get(const.USE_EARLY_STOPPING, True) and os.path.exists(self.trainingArgs.best_model_dir):
                shutil.rmtree(self.trainingArgs.best_model_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup training artifacts: {str(e)}")

        base_path = os.path.join(os.path.dirname(self.trainingArgs.output_dir), const.METRICS)
        metrics_file = os.path.join(base_path, const.TRAINING_PROGRESS_FILE)
        learning_curve_file = os.path.join(base_path, const.LEARNING_CURVE_FILE)
        try:
            if os.path.exists(metrics_file):
                metrics_df = pd.read_csv(metrics_file)
                epochs = range(1, len(metrics_df) + 1)
                
                plt.figure(figsize=(10, 6))
                
                # Plot loss curves
                plt.subplot(2, 1, 1)
                plt.plot(epochs, metrics_df['train_loss'], 'b-', label='Training Loss')
                plt.plot(epochs, metrics_df['eval_loss'], 'orange', label='Evaluation Loss')
                plt.title('Learning Curves')
                plt.xlabel('Epoch')
                plt.ylabel('Loss')
                plt.legend()
                plt.grid(True)
                
                # Plot MCC curve
                plt.subplot(2, 1, 2)
                plt.plot(epochs, metrics_df['mcc'], 'g-', label='Evaluation MCC')
                plt.xlabel('Epoch')
                plt.ylabel('MCC Score')
                plt.legend()
                plt.grid(True)
                
                plt.tight_layout()
                plt.savefig(learning_curve_file)
                plt.close()
                
                logger.info(f"Generated learning curves plot at {learning_curve_file}")
            else:
                logger.warning(f"Training Progress file not found at {metrics_file}")
        except Exception as e:
            logger.warning(f"Failed to generate learning curves: {str(e)}")

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
