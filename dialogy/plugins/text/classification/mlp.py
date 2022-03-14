"""
.. _mlp_classifier:

This module provides a trainable MLP classifier.
"""
import ast
import operator
import os
from pprint import pformat
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd
from sklearn.exceptions import NotFittedError
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, make_scorer
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection._search import BaseSearchCV
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from tqdm import tqdm

tqdm.pandas()

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.plugins.text.classification.tokenizers import identity_tokenizer
from dialogy.types import Intent
from dialogy.utils import load_file, logger, save_file


class MLPMultiClass(Plugin):
    """
    This plugin provides a classifier based on sklearn's MLPClassifier.

    .. _MLPMultiClass:
    """

    def __init__(
        self,
        model_dir: str,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
        threshold: float = 0.1,
        score_round_off: int = 5,
        purpose: str = const.TRAIN,
        fallback_label: str = const.ERROR_LABEL,
        data_column: str = const.DATA,
        label_column: str = const.LABELS,
        args_map: Optional[Dict[str, Any]] = None,
        skip_labels: Optional[List[str]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:

        super().__init__(dest=dest, guards=guards, debug=debug)
        self.model_pipeline: Any = None
        self.fallback_label = fallback_label
        self.data_column = data_column
        self.label_column = label_column
        self.mlp_model_path = os.path.join(model_dir, const.MLPMODEL_FILE)
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
            if os.path.exists(self.mlp_model_path):
                self.init_model()
        except EOFError:  # pragma: no cover
            logger.error(  # pragma: no cover
                f"Plugin {self.__class__.__name__} Failed to load MLPClassifier Model from {self.mlp_model_path}. "
                "Ignore this message if you are training but if you are using this in production or testing, then this is serious!"
            )

    def init_model(self, param_search: BaseSearchCV = GridSearchCV) -> Dict[str, Any]:
        """
        Initialize the model if artifacts are available.
        """
        if os.path.exists(self.mlp_model_path):
            self.load()
            return {}
        args = (
            self.args_map[self.purpose]
            if self.args_map and self.purpose in self.args_map
            else {}
        )

        pipeline = Pipeline(
            [
                (
                    const.TFIDF,
                    TfidfVectorizer(
                        tokenizer=identity_tokenizer,
                        stop_words=const.STOPWORDS,
                        lowercase=const.TFIDF_LOWERCASE,
                        ngram_range=const.DEFAULT_NGRAM,
                    ),
                ),
                (
                    const.MLP,
                    MLPClassifier(
                        random_state=const.MLP_RANDOMSTATE,
                        max_iter=(
                            args[const.NUM_TRAIN_EPOCHS]
                            if args
                            else const.MLP_DEFAULT_TRAIN_EPOCHS
                        ),
                        verbose=True,
                    ),
                ),
            ]
        )
        USE = "use"
        if args and args[const.USE_GRIDSEARCH][USE]:
            GRID = self.get_gridsearch_grid(
                pipeline, **args[const.USE_GRIDSEARCH][const.PARAMS]
            )
            self.model_pipeline = param_search(
                estimator=pipeline,
                param_grid=GRID,
                cv=args[const.USE_GRIDSEARCH][const.CV],
                n_jobs=const.GRIDSEARCH_WORKERS,
                verbose=args[const.USE_GRIDSEARCH][const.VERBOSE_LEVEL],
                scoring=make_scorer(f1_score, average=const.GRID_SCORETYPE),
                return_train_score=True,
            )
        else:
            self.model_pipeline = pipeline

        return args

    def get_gridsearch_grid(
        self, pipeline: Pipeline, **kwargs: Any
    ) -> List[Dict[str, List[Any]]]:
        """
        Gets gridsearch hyperparameters for the model in proper grid params format.

        Raises:
            ValueError: If a gridsearch parameter doesn't exist in sklearns TFIDF and MLPClassifier modules.
        """
        grid_params: Dict[str, List[Any]] = {}
        tfidf_params = pipeline[const.TFIDF].get_params().keys()
        mlp_params = pipeline[const.MLP].get_params().keys()
        for k, v in kwargs.items():
            if k not in tfidf_params and k not in mlp_params:
                raise ValueError(
                    f"Hyperparam defined for gridsearch {k} doesn't exist,\nRefer: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html\nand https://scikit-learn.org/stable/modules/generated/sklearn.neural_network.MLPClassifier.html"
                )
            if k != const.NGRAM_RANGE:
                grid_params[f"{const.MLP}__{k}"] = self.get_formatted_gridparams(v)
            else:
                grid_params[f"{const.TFIDF}__{k}"] = self.get_formatted_gridparams(v)

        return [grid_params]

    @staticmethod
    def get_formatted_gridparams(params: List[Any]) -> List[Any]:
        """
        Gets the valid parameters for the gridsearch.

        Args:
            values: The values to be validated.

        Returns:
            The valid parameters.
        """
        valid_params: List[Any] = []
        for p in params:
            try:
                valid_params.append(ast.literal_eval(p))
            except ValueError:
                valid_params.append(p)
        return valid_params

    @property
    def valid_mlpmodel(self) -> bool:
        return hasattr(self.model_pipeline, "classes_")

    def inference(self, texts: Optional[List[str]]) -> List[Intent]:
        """
        Predict the intent of a list of texts.

        :param texts: A list of strings, derived from ASR transcripts.
        :type texts: List[str]
        :raises AttributeError: In case the model isn't of sklearn pipeline or gridsearchcv.
        :return: A list of intents corresponding to texts.
        :rtype: List[Intent]
        """
        logger.debug(f"Classifier input:\n{texts}")
        fallback_output = Intent(name=self.fallback_label, score=1.0).add_parser(self)

        if self.model_pipeline is None:
            logger.error(f"No model found for plugin {self.__class__.__name__}!")
            return [fallback_output]

        if not texts:
            return [fallback_output]

        if not isinstance(self.model_pipeline, Pipeline) and not isinstance(
            self.model_pipeline, GridSearchCV
        ):
            raise AttributeError(
                "Seems like you forgot to "
                f"save the {self.__class__.__name__} plugin."
            )

        try:
            probs_and_classes = sorted(
                zip(
                    self.model_pipeline.predict_proba(texts)[0],
                    self.model_pipeline.classes_,
                ),
                key=operator.itemgetter(0),
                reverse=True,
            )
        except NotFittedError:
            logger.error(f"{self.__class__.__name__} model not trained yet!")
            return [fallback_output]

        return [
            Intent(name=intent, score=round(score, self.round)).add_parser(self)
            for score, intent in probs_and_classes
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

    def train(
        self, training_data: pd.DataFrame, param_search: BaseSearchCV = GridSearchCV
    ) -> None:
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

        if self.valid_mlpmodel:
            logger.warning(
                f"Model already exists on {self.mlp_model_path}"
            )  # pragma: no cover
            return  # pragma: no cover

        skip_labels_filter = training_data[self.label_column].isin(self.skip_labels)
        training_data = training_data[~skip_labels_filter].copy()

        self.labels_num = training_data[self.label_column].nunique()
        sample_size = 5 if len(training_data) > 5 else len(training_data)
        training_data.rename(
            columns={self.data_column: const.TEXT, self.label_column: const.LABELS},
            inplace=True,
        )
        args = self.init_model(param_search=param_search)
        logger.debug(
            f"Displaying a few samples (this goes into the model):\n{training_data.sample(sample_size)}\nLabels: {self.labels_num}."
        )

        self.model_pipeline.fit(training_data[const.TEXT], training_data[const.LABELS])
        USE = "use"
        if args and args[const.USE_GRIDSEARCH][USE]:
            logger.debug(
                f"Best gridsearch params found:\n{pformat(self.model_pipeline.best_params_)}"
            )
        self.save()

    def save(self) -> None:
        """
        Save the plugin artifacts.

        :raises ValueError: In case the mlp model is not trained.
        """
        if not self.model_pipeline or not self.valid_mlpmodel:
            raise ValueError(
                f"Plugin {self.__class__.__name__} seems to be un-trained."
            )
        save_file(
            self.mlp_model_path,
            self.model_pipeline,
            mode="wb",
            writer=joblib.dump,
        )

    def load(self) -> None:
        """
        Load the plugin artifacts.
        """
        self.model_pipeline = load_file(
            self.mlp_model_path, mode="rb", loader=joblib.load
        )

    def utility(self, input: Input, _: Output) -> Any:
        return self.inference(
            input.clf_feature
        )  # pylint: disable=no-value-for-parameter
