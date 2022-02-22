"""
.. _RetainOriginalIntentPlugin:

We may apply transforms over predicted intents. This makes it hard to track the impact of classifiers. 
Here, we will track the original intent, the one produced by a classifier.
"""
from typing import List, Optional
from dialogy.base import Output, Plugin, Guard, Input
from dialogy.base.output import ORIGINAL_INTENT_TYPE
from dialogy.types import Intent
from dialogy import constants as const


class RetainOriginalIntentPlugin(Plugin):
    def __init__(
        self,
        replace_output: bool = False,
        dest: Optional[str] = "output.original_intent",
        guards: Optional[List[Guard]] = None,
        debug: bool = False
    ) -> None:
        super().__init__(replace_output=replace_output, dest=dest, guards=guards, debug=debug)

    def retain(self, intents: List[Intent]) -> ORIGINAL_INTENT_TYPE:
        if not intents:
            return {}

        if not isinstance(intents, list):
            return {}

        intent, *_ = intents
        return {
            const.NAME: intent.name,
            const.SCORE: intent.score
        }

    def utility(self, _: Input, output: Output) -> ORIGINAL_INTENT_TYPE:
        return self.retain(output.intents)
