"""
.. _calibration_plugin:

This module provides a plugin to calibrate the ASR output. We look for Acoustic model and Language model scores of the ASR
and predict the quality of the transcripts. Poor transcripts are filtered out. This plugin ships a trainable component.
"""
import math
import pickle
from typing import Any, Dict, List, Optional

import numpy as np

from dialogy import constants as const
from dialogy.base.plugin import Plugin
from dialogy.types import PluginFn, Transcript, Utterance
from dialogy.utils import load_file, normalize


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
            self.vectorizer = load_file(
                file_path=vectorizer_path, mode="rb", loader=pickle.load
            )
        if classifier:
            self.classifier = classifier
        else:
            self.classifier = load_file(
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

    def filter_asr_output(self, utterances: List[Utterance], lang: str) -> List[str]:
        """
        .. _filter_asr_output:

        Filter ASR output to return alternatives considered safe for classification.

        The good alternatives are decided by the pWER (predicted WER). If the pWER is less than
        the `threshold`.
        Also returns the list of predicted wers.

        .. ipython:: python

            import numpy as np
            from scipy import sparse
            from dialogy.plugins import WERCalibrationPlugin
            from dialogy.plugins.text.calibration import WERCalibrationConfig
            from dialogy.workflow.workflow import Workflow
            from dialogy import constants as const

            utterances = [[{"transcript": "This is a sentence", "am_score":230, "lm_score":50},
                                    {"transcript": "This is another sentence", "am_score":300, "lm_score":400}]]
            lang = "en"

            # This is just to mock the vectorizer and classifier
            # We don't need to use them in a realistic cases
            # In a realistic scenario we need to load
            # these from pickle files
            #
            # and...
            #
            # the ideal config object looks like:
            # config = {
            #    "en": {
            #        "threshold": 0.5,
            #        "vectorizer_path": "path/to/vectorizer.pkl",
            #        "classifier_path": "path/to/classifier.pkl",
            #    }
            # }
            # but since we have items mocked, we will be using the mocks directly

            class MyClassifier(object):
                def predict(self, X):
                    return np.array([1])
            classifier = MyClassifier()
            class MyVectorizer(object):
                def transform(self, text):
                    assert isinstance(text, list)
                    return sparse.csr_matrix(np.array([1]))
            vectorizer = MyVectorizer()
            def mutate(workflow, value):
                workflow.input = value
            config = {}
            plugin = WERCalibrationPlugin(config, access=lambda _: (utterances, lang), mutate=mutate, debug=True)
            plugin.config[lang] = WERCalibrationConfig(
                vectorizer=vectorizer, classifier=classifier, threshold=1.5
            )
            workflow = Workflow([plugin])
            workflow.run(input_=utterances)


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
        if (
            vectorizer is None
            or classifier is None
            or average_word_count <= const.WORD_THRESHOLD
        ):
            return normalize(utterances)

        return normalize(
            [
                [
                    alternative
                    for alternative in utterance
                    if predict_alternative(alternative, vectorizer, classifier)
                    < threshold
                ]
                for utterance in utterances
            ]
        )

    def utility(self, *args: Any) -> Any:
        return self.filter_asr_output(*args)
