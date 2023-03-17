"""
.. OOSFilter: Mutate an incoming intent to out-of-scope intent (OOS) if the score of the predicted intent is less than certain threshold

Expects 2 mandatory arguments:
1. intent_oos -> str
2. threshold value -> float
"""

from typing import Any, List, Optional

from dialogy.base.plugin import Input, Output, Plugin, Guard
from dialogy.types import Intent


class OOSFilterPlugin(Plugin):
    def __init__(
        self,
        threshold: float,
        intent_oos: str,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        **kwargs
    ) -> None:
        super().__init__(dest=dest, guards=guards, **kwargs)

        if not threshold or not intent_oos:
            raise TypeError(
                "Thereshold and intent_oos are mandatory arguments for the OOSFilterPlugin"
            )

        self.threshold = threshold
        self.intent_oos = intent_oos

    def set_oos_intent(self, intents: List[Intent]) -> List[Intent]:
        if not intents:
            raise TypeError(
                "Either OOSFilter was added before the intent classifier plugin or the intents list is empty"
            )

        if intents[0].score < self.threshold:
            intents[0].name = self.intent_oos
        return intents

    def utility(self, input_: Input, output: Output) -> List[Intent]:
        return self.set_oos_intent(output.intents)
