"""
We attempt to denoise the intent labels by employing different approaches:

1. Drop data points where same utterance is tagged with two different labels in two different data points.

Make sure that you add this plugin as the very first plugin.
"""
import json
from typing import Any, List, Optional

import pandas as pd
from loguru import logger
import hashlib
import pickle

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin


class LabelDenoiserPlugin(Plugin):
    """
    .. _LabelDenoiserPlugin:

    Working details are covered in :ref:`LabelDenoiserPlugin<LabelDenoiserPlugin>`.

    :param Plugin: [description]
    :type Plugin: [type]
    """

    def __init__(
        self,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
        drop_conflicting_labels: bool = True,
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )
        self.drop_conflicting_labels = drop_conflicting_labels

    @staticmethod
    def identify_conflicting_labels(training_data: pd.DataFrame) -> pd.DataFrame:

        logger.debug(f"Finding data points with conflicting labels...")

        training_data["frozen_set_hash"] = training_data["alternatives"].apply(
            lambda x: hashlib.md5(
                pickle.dumps(
                    sorted(frozenset((alt["transcript"] for alt in json.loads(x)[0])))
                )
            ).hexdigest()
        )

        hash_with_different_intents_tagged = {}

        training_data = training_data[training_data["tag"] != "_audio_issue_"]

        for _, row in training_data.iterrows():

            frozen_set_hash = row["frozen_set_hash"]
            tagged_intent = row["tag"]

            if tagged_intent == "_audio_issue_":
                continue

            if frozen_set_hash not in hash_with_different_intents_tagged:
                hash_with_different_intents_tagged[frozen_set_hash] = {tagged_intent: 1}
            else:
                conflicting_intents = hash_with_different_intents_tagged[
                    frozen_set_hash
                ]
                if tagged_intent in conflicting_intents:
                    conflicting_intents[tagged_intent] += 1
                else:
                    conflicting_intents[tagged_intent] = 1

        filtered_hash_with_different_intents_tagged = {
            k: v for k, v in hash_with_different_intents_tagged.items() if len(v) > 1
        }

        training_data["conflicting_intents"] = training_data["frozen_set_hash"].map(
            filtered_hash_with_different_intents_tagged
        )
        training_data["use"] = training_data["conflicting_intents"].isna()

        return training_data

    def utility(self, input: Input, _: Output) -> Any:
        return

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        if not self.use_transform:
            return training_data

        training_data["use"] = True
        logger.debug(f"Transforming dataset via {self.__class__.__name__}")

        if self.drop_conflicting_labels:
            training_data = self.identify_conflicting_labels(training_data)

        training_data_ = training_data[training_data.use].copy()
        training_data_.drop("use", axis=1, inplace=True)
        discarded_data = len(training_data) - len(training_data_)
        if discarded_data:
            logger.debug(
                f"Discarding {discarded_data} samples out of {len(training_data)} because of conflicting labels."
            )
        return training_data_
