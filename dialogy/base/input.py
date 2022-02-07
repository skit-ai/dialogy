from __future__ import annotations
from typing import Optional, List

import attr

from dialogy.types import Utterance
from dialogy.utils import is_unix_ts, normalize, is_utterance


@attr.frozen
class Input:
    utterances: List[Utterance] = attr.ib(kw_only=True)

    reference_time: Optional[int] = attr.ib(default=None, kw_only=True)
    latent_entities: bool = attr.ib(default=False, kw_only=True, converter=bool)
    transcripts: List[str] = attr.ib(default=None)
    clf_feature: Optional[List[str]] = attr.ib(
        kw_only=True,
        factory=list,
        validator=attr.validators.optional(attr.validators.instance_of(list)),
    )
    lang: str = attr.ib(default="en", kw_only=True, validator=attr.validators.instance_of(str))
    locale: str = attr.ib(
        default="en_IN",
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    timezone: str = attr.ib(
        default="UTC",
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    slot_tracker: Optional[list] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(list)),
    )
    current_state: Optional[str] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    previous_intent: Optional[str] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )

    def __attrs_post_init__(self):
        try:
            object.__setattr__(self, "transcripts", normalize(self.utterances))
        except TypeError:
            ...

    @reference_time.validator
    def _check_reference_time(self, attribute: attr.Attribute, reference_time: int):
        if reference_time is None:
            return
        if not isinstance(reference_time, int):
            raise TypeError(f"{attribute.name} must be an integer.")
        if not is_unix_ts(reference_time):
            raise ValueError(f"{attribute.name} must be a unix timestamp but got {reference_time}.")

    def json(self):
        return attr.asdict(self)

    @classmethod
    def from_dict(cls, d: dict, reference: Optional[Input] = None):
        if reference:
            return attr.evolve(reference, **d)
        return attr.evolve(cls(utterances=d["utterances"]), **d)
