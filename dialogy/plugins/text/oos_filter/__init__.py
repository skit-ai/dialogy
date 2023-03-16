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
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        threshold: float = 0.5,
        intent_oos: str = "_oos_",
        **kwargs
    ) -> None:
        super().__init__(dest=dest, guards=guards, **kwargs)
        self.threshold = threshold
        self.intent_oos = intent_oos

    def set_oos_intent(self, intents: List[Intent]) -> List[Intent]:
        if intents[0].score < self.threshold:
            intents[0].name = self.intent_oos
        return intents

    def utility(self, input_: Input, output: Output) -> List[Intent]:
        return self.set_oos_intent(output.intents)
