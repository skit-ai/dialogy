"""
This module provides utilities to handle multiple intents from each
alternative from the ASR.
"""
from collections import Counter
from typing import List

import attr
import numpy as np

from dialogy import constants as const
from dialogy.plugin import Plugin
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.workflow import Workflow


@attr.s
class VotePlugin(Plugin):
    """
    An instance of VoteIntentPlugin helps in voting for a strong
    evidence over other candidates.

    This plugin takes into consideration a list of predictions (signals)
    some of which can be strong, (decided by their confidence score for now)
    and weak signals are filtered out. If there is a healthy vote proportion,
    we will consider the winning signal as the true output.

    This class handles signals which are produced by an intent classifier that
    classifies a set of ASR alternatives (strings).

    The voting algorithm here is naive as it is based on heuristics
    and plain counting. This can be improved by using learned trees/forests.

    Ideal design should provide the signals, their strengths (confidence) and
    signal boosters, any contextual information that implies a weak signal has
    more weight than its counterparts.
    """

    fallback_intent: str = attr.ib(default=const.S_INTENT_OOS)
    constituency: float = attr.ib(default=0.5)
    threshold: float = attr.ib(default=0.9)

    def vote_signal(self, intents: List[Intent]) -> Intent:
        """
        Reduce a list of intents.

        This is a naive voting algorithm. We filter intents with high confidence.
        Count the frequency of the remaining intents. If the proportion of votes
        goes beyond the expected constituency, then the intent is elected else
        a fallback intent is emitted.

        Args:
            intents (List[Intent]): A list of predictions over ASR output. (size ~ 1-10)
            constituency (float, optional): Threshold for proportion of votes,
                proportion over this qualifies an intent for victory. Defaults to 0.5.

        Returns:
            Intent: Voted signal or fallback in case of no consensus.
        """
        fallback = Intent(name=self.fallback_intent, score=1)
        if not intents:
            return fallback

        qualified_intents = [
            intent.name for intent in intents if intent.score > self.threshold
        ]
        candidates = len(qualified_intents)
        ballot = Counter(qualified_intents)

        # victory is a list of tuples like:
        # [("name", 4)], where 4 is the frequency.
        victory = ballot.most_common(1)

        # To defend against Counter init with `[]`.
        # due to the filter.
        if not victory:
            return fallback

        # We want the name of the winning entry.
        # and the votes it received.
        winner, votes = victory[0]

        if votes:
            # don't divide by 0
            proportion = votes / candidates
            if proportion > self.constituency:
                return Intent(
                    name=winner,
                    score=float(
                        np.mean(
                            [
                                intent.score
                                for intent in intents
                                if intent.name == winner
                            ]
                        )
                    ),
                )
        return Intent(name=self.fallback_intent, score=1)

    def plugin(self, workflow: Workflow) -> None:
        """
        Plugin to ease workflow io.
        """
        access = self.access
        mutate = self.mutate

        if access and mutate:
            intents = access(workflow)
            intent = self.vote_signal(intents)
            mutate(workflow, intent)
        else:
            raise TypeError(
                "Expected `access` and `mutate` to be Callable,"
                f" got access={type(access)} mutate={type(mutate)}"
            )

    def __call__(self) -> PluginFn:
        """
        Convenience.
        """
        return self.plugin
