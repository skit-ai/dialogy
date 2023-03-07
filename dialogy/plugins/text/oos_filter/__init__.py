"""
.. OOSFilter: Mutate an incoming intent to out-of-scope intent (OOS) if the score of the predicted intent is less than certain threshold

Expects 2 mandatory arguments:
1. intent_oos -> str
2. threshold value -> float
"""

from typing import Any, Callable, Dict, List, Optional
from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types import Intent


class OOSFilterPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        guards=None,
        threshold: float = None,
        intent_oos: str = None,
        **kwargs
    ) -> None:
        super().__init__(dest=dest, guards=guards, **kwargs)
        self.threshold = threshold
        self.intent_oos = intent_oos

    def set_oos_intent(self, intents: List[Intent]) -> Any:
        if intents[0].score < self.threshold:
            intents[0].name = self.intent_oos
        return intents

    def utility(self, input_: Input, output: Output) -> Any:
        return self.set_oos_intent(output.intents)
