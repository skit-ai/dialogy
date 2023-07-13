"""
.. OOSFilter: Mutate an incoming intent to out-of-scope intent (OOS) if the score of the predicted intent is less than certain threshold

Expects 2 mandatory arguments:
1. intent_oos -> str
2. threshold value -> float
"""

from typing import Any, List, Optional, Union

from dialogy.base.plugin import Input, Output, Plugin, Guard
from dialogy.types import Intent
from dialogy.utils import logger
import yaml


class OOSFilterPlugin(Plugin):
    def __init__(
        self,
        intent_oos: str,
        intent_threshold_map_path: Optional[str] = None,
        dest: Optional[str] = None,
        threshold: Optional[float] = None,
        guards: Optional[List[Guard]] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(dest=dest, guards=guards, **kwargs)

        if not isinstance(intent_oos, str):
            raise TypeError(
                f"intent_oos type should be string, received {type(intent_oos)}"
            )

        if threshold and not isinstance(threshold, float):
            raise TypeError(
                f"Threshold type should be float, received {type(threshold)}"
            )

        if intent_threshold_map_path and not isinstance(intent_threshold_map_path, str):
            raise TypeError(
                f"intent_threshold_map_path type should be string, \
                received {type(intent_threshold_map_path)}"
            )

        if not threshold and not intent_threshold_map_path:
            raise TypeError(
                "Both threshold and intent_threshold_map_path cannot be empty. \
                Please give either one."
            )

        self.threshold = threshold
        self.intent_oos = intent_oos

        self.intent_threshold_map = None
        if intent_threshold_map_path and self.purpose != "train":
            with open(intent_threshold_map_path, "r") as f:
                self.intent_threshold_map = yaml.safe_load(f)

        if self.threshold and self.intent_threshold_map:
            self.threshold = None
            logger.warning(
                "Both threshold and the intent_threshold_map have been instantiated \
                The threshold value is being overriden to None."
            )

    def set_oos_intent(self, intents: List[Intent]) -> List[Intent]:
        if not intents:
            raise ValueError(
                "Either OOSFilter was added before the intent classifier plugin or the intents list is empty"
            )

        intent_name = intents[0].name
        intent_score = intents[0].score

        if (
            self.threshold
            and intent_score < self.threshold
            or (
                self.intent_threshold_map
                and intent_name in self.intent_threshold_map
                and intent_score < self.intent_threshold_map[intent_name]
            )
        ):
            intents[0].name = self.intent_oos

        return intents

    async def utility(self, input_: Input, output: Output) -> List[Intent]:
        return self.set_oos_intent(output.intents)
