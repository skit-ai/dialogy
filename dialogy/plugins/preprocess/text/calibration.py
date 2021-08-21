"""
.. _calibration_plugin:

This module provides a plugin to calibrate the ASR output. We look for Acoustic model and Language model scores of the ASR
and predict the quality of the transcripts. Poor transcripts are filtered out. This plugin ships a trainable component.
"""
import math
import pickle
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from dialogy import constants as const
from dialogy.base.plugin import Plugin
from dialogy.types.plugin import PluginFn
from dialogy.utils.file_handler import safe_load


def predict_alternative(
    alternative: Dict[str, Any], vectorizer: Any, classifier: Any
) -> float:
    vec_ = vectorizer.transform([alternative[const.TRANSCRIPT]]).todense().tolist()[0]
    n_words = len(alternative[const.TRANSCRIPT].split())
    am_score = alternative[const.AM_SCORE]
    lm_score = alternative[const.LM_SCORE]
    features = [
        am_score / n_words,
        lm_score / n_words,
        alternative[const.TRANSCRIPT].count("UNK"),
        n_words,
        am_score / math.log(1 + n_words),
        lm_score / math.log(1 + n_words),
        am_score / math.sqrt(n_words),
        lm_score / math.sqrt(n_words),
    ]
    return classifier.predict(np.array([vec_ + features])).tolist()[0]


class WERCalibrationConfig:
    """
    Config object for WERCalibrationPlugin.
    """

    def __init__(
        self,
        threshold: float = 0.5,
        vectorizer: Any = None,
        classifier: Any = None,
        vectorizer_path: Optional[str] = None,
        classifier_path: Optional[str] = None,
    ):
        self.threshold = threshold
        if vectorizer:
            self.vectorizer = vectorizer
        else:
            self.vectorizer = safe_load(
                file_path=vectorizer_path, mode="rb", loader=pickle.load
            )
        if classifier:
            self.classifier = classifier
        else:
            self.classifier = safe_load(
                file_path=classifier_path, mode="rb", loader=pickle.load
            )


class WERCalibrationPlugin(Plugin):
    """
    .. _WERCalibrationPlugin:

    Plugin to calibrate the ASR output.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        debug: bool = False,
    ) -> None:
        super().__init__(access=access, mutate=mutate, debug=debug)
        self.config: Dict[str, WERCalibrationConfig] = {}
        for lang in config:
            self.config[lang] = WERCalibrationConfig(**config[lang])

    def filter_asr_output(
        self, utterances: List[List[Dict[str, Any]]], lang: str
    ) -> Dict[str, Any]:
        """
        .. _filter_asr_output:

        Filter ASR output to return alternatives considered safe for classification.

        The good alternatives are decided by the pWER (predicted WER). If the pWER is less than
        the `threshold`.
        Also returns the list of predicted wers.

        .. ipython:: python

            from dialogy.plugins.preprocess.text.calibration import filter_asr_output

            utterances = [[{"transcript": "This is a sentence", "am_score":230, "lm_score":100}, \
                                {"transcript": "This is another sentence", "am_score":230, "lm_score":100}]]
            filter_asr_output(utterances)

        :param utterances: A structure representing ASR output. We support only:

            1. :code:`List[List[Dict[str, Any]]]`

        :type utterances: List[List[Dict[str, Any]]]
        :return: Good alternatives, predicted wers
        :rtype: Tuple[List[List[Dict[str, Any]]], List[float]]
        :raises: `AssertionError` if utterance isn't in the desired format.
        """
        vectorizer = self.config[lang].vectorizer
        classifier = self.config[lang].classifier
        threshold = self.config[lang].threshold

        if vectorizer is None or classifier is None:
            return {
                const.ALTERNATIVES: utterances,
                const.PWER: [0.0] * len(utterances[0]),
            }

        valid_alternatives = []
        pred_wers = []
        for utterance in utterances:
            res = []
            for alternative in utterance:
                pred_wer = predict_alternative(alternative, vectorizer, classifier)
                pred_wers.append(pred_wer)
                if pred_wer < threshold:
                    res.append(alternative)
            valid_alternatives.append(res)
        return {const.ALTERNATIVES: valid_alternatives, const.PWER: pred_wers}

    def utility(self, *args: Any) -> Any:
        return self.filter_asr_output(*args)
