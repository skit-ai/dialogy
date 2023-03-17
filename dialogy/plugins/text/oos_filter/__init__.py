"""
.. OOSFilter: Mutate an incoming intent to out-of-scope intent (OOS) if the score of the predicted intent is less than certain threshold

Expects 2 mandatory arguments:
1. intent_oos -> str
2. threshold value -> float
"""

from typing import Any, List, Optional, Union

from dialogy.base.plugin import Input, Output, Plugin, Guard
from dialogy.types import Intent


class OOSFilterPlugin(Plugin):
    def __init__(
        self,
        threshold: float,
        intent_oos: str,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        **kwargs: Any
    ) -> None:
        super().__init__(dest=dest, guards=guards, **kwargs)

        if not isinstance(threshold, float):
            raise TypeError(
                f"Threshold type should be float, received {type(threshold)}"
            )
        
        if not isinstance(intent_oos, str):
            raise TypeError(
                f"Threshold type should be float, received {type(intent_oos)}"
            )

        self.threshold = threshold
        self.intent_oos = intent_oos

    def set_oos_intent(self, intents: List[Intent]) -> List[Intent]:
        if not intents:
            raise ValueError(
                "Either OOSFilter was added before the intent classifier plugin or the intents list is empty"
            )

        if intents[0].score < self.threshold:
            intents[0].name = self.intent_oos
        return intents

    def utility(self, input_: Input, output: Output) -> List[Intent]:
        return self.set_oos_intent(output.intents)
