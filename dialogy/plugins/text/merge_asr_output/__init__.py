"""
We expect ASR transcripts to be the most common inputs to the system. Since there is a chance that we can improve the
performance by asking the ASR to provide more information in the form of multiple alternatives. The problem though, is
they can't be used as it is. Models that can operate on text data, need them to be vectorized. These vectors have
semantic significance, where different text inputs imply different vectors. If their semantic differences are modeled
well, we can expect these vectors to be similar or dissimilar just like the text that was used to create them.

The problem with transcripts is, there **will** be noise in the transcripts, since we asked for :code:`N` transcripts,
by definition, an ASR will provide N unique transcripts. The noise may in fact be inconsequential for downstream NLP
tasks, but we have noticed that there are certain inputs owing to audio artifacts or state of LMs tend to have a great
impact on the transcription.

This module will ship a simple concatenation strategy to address this problem. The NLP model should be expected to
handle documents (:code:`List[str]`) instead of single text. The plugin then will be able to produce a :code:`str` by
simply concatenation of each transcript.

This may not be very helpful, there is a :ref:`VotePlugin <vote_plugin>` under development so use it with caution. It may
help with precision at the cost of recall.
"""
import json
import traceback
from logging import log
from typing import Any, List, Optional

import pandas as pd  # type: ignore

import dialogy.constants as const
from dialogy.base.plugin import Plugin, PluginFn
from dialogy.utils import logger, normalize


# == merge_asr_output ==
def merge_asr_output(utterances: Any) -> List[str]:
    """
    .. _merge_asr_output:

    Join ASR output to single string.

    This function provides a merging strategy for n-best ASR transcripts by
    joining each transcript, such that:

    - each sentence end is marked by " </s>" and,
    - sentence start marked by " <s>".

    The key "transcript" is expected in the ASR output, the value of which would be operated on
    by this function.

    The normalization is done by :ref:`normalize<normalize>`

    .. ipython:: python

        from dialogy.plugins.text.merge_asr_output import merge_asr_output

        utterances = ["This is a sentence", "That is a sentence"]
        merge_asr_output(utterances)

    :param utterances: A structure representing ASR output. We support only:

        1. :code:`List[str]`
        2. :code:`List[List[str]]`
        3. :code:`List[List[Dict[str, str]]]`
        4. :code:`List[Dict[str, str]]`

    :type utterances: Any
    :return: Concatenated string, separated by <s> and </s> at respective terminal positions of each sentence.
    :rtype: List[str]
    :raises: TypeError if transcript is missing in cases of :code:`List[List[Dict[str, str]]]` or
        :code:`List[Dict[str, str]]`.
    """
    try:
        flat_representation: List[str] = normalize(utterances)
        return ["<s> " + " </s> <s> ".join(flat_representation) + " </s>"]
    except TypeError as type_error:
        raise TypeError("`transcript` is expected in the ASR output.") from type_error


class MergeASROutputPlugin(Plugin):
    """
    .. _merge_asr_output_plugin:

    Working details are covered in :ref:`merge_asr_output <merge_asr_output>`.

    :param Plugin: [description]
    :type Plugin: [type]
    """

    def __init__(
        self,
        access: Optional[PluginFn],
        mutate: Optional[PluginFn],
        debug: bool = False,
    ) -> None:
        super().__init__(access, mutate, debug=debug)
        self.data_column = "data"

    def utility(self, *args: Any) -> Any:
        return merge_asr_output(*args)

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        training_data["use"] = True
        logger.debug("Transforming training data.")
        for i, row in training_data.iterrows():
            try:
                asr_output = json.loads(row[self.data_column]).get(
                    const.ALTERNATIVES, []
                )
                if asr_output:
                    training_data.loc[i, self.data_column] = merge_asr_output(
                        asr_output
                    )[0]
                else:
                    training_data.loc[i, "use"] = False
            except Exception as error:  # pylint: disable=broad-except
                training_data.loc[i, "use"] = False
                logger.error(f"{error}\n{traceback.format_exc()}")

        training_data_ = training_data[training_data.use]
        discarded_data = len(training_data) - len(training_data_)
        logger.debug(
            f"Discarding {discarded_data} samples because the alternatives couldn't be parsed."
        )
        return training_data_