"""
We use classifiers for prediction of :ref:`intents<Intent>`, utterances from an ASR are prominent features
for the task. We featurize the utterances by concatenation of all transcripts.

.. ipython::

    In [1]: from dialogy.workflow import Workflow
       ...: from dialogy.plugins import MergeASROutputPlugin
       ...: from dialogy.base import Input

    In [2]: merge_asr_output_plugin = MergeASROutputPlugin(dest="input.clf_feature")
       ...: workflow = Workflow([merge_asr_output_plugin])

    In [3]: input_, _ = workflow.run(Input(utterances=["we will come by 7 pm", " will come by 7 pm"]))

    In [4]: input_
"""
import json
import traceback
from typing import Any, List, Optional

import pandas as pd
from loguru import logger
from tqdm import tqdm

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.utils import normalize


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
        transcripts: List[str] = normalize(utterances)
        invalid_transcript = len(transcripts) == 1 and any(
            token.lower() in transcripts for token in const.INVALID_TOKENS
        )
        if invalid_transcript or not transcripts:
            return []
        else:
            return ["<s> " + " </s> <s> ".join(transcripts) + " </s>"]
    except TypeError as type_error:
        raise TypeError("`transcript` is expected in the ASR output.") from type_error


class MergeASROutputPlugin(Plugin):
    """
    .. _MergeASROutputPlugin:

    Working details are covered in :ref:`MergeASROutputPlugin<MergeASROutputPlugin>`.

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
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )

    def utility(self, input: Input, _: Output) -> Any:
        return merge_asr_output(input.utterances)

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        if not self.use_transform:
            return training_data

        training_data["use"] = True
        logger.debug(f"Transforming dataset via {self.__class__.__name__}")
        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            asr_output = None
            try:
                asr_output = json.loads(row[self.input_column])
                if asr_output and (merged_asr_ouptut := merge_asr_output(asr_output)):
                    training_data.loc[i, self.output_column] = merged_asr_ouptut[0]
                else:
                    training_data.loc[i, "use"] = False
            except Exception as error:  # pylint: disable=broad-except
                training_data.loc[i, "use"] = False
                logger.error(f"{error} -- {asr_output}\n{traceback.format_exc()}")

        training_data_ = training_data[training_data.use].copy()
        training_data_.drop("use", axis=1, inplace=True)
        discarded_data = len(training_data) - len(training_data_)
        if discarded_data:
            logger.debug(
                f"Discarding {discarded_data} samples because the alternatives couldn't be parsed."
            )
        return training_data_
