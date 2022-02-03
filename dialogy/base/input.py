from typing import Optional, List

import attr

from dialogy.types import Utterance
from dialogy.utils import is_unix_ts, normalize, is_utterance


@attr.frozen
class Input:
    utterances: List[Utterance] = attr.ib(kw_only=True)
    reference_time: Optional[int] = attr.ib(kw_only=True)

    latent_entities: bool = attr.ib(default=False, kw_only=True, converter=bool)
    transcripts: List[str] = attr.ib(default=None)
    clf_feature: Optional[str] = attr.ib(
        kw_only=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
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
        object.__setattr__(self, "transcript", normalize(self.utterances))

    @reference_time.validator
    def _check_reference_time(self, attribute: attr.Attribute, reference_time: int):
        if not isinstance(reference_time, int):
            raise TypeError(f"{attribute.name} must be an integer.")
        if not is_unix_ts(reference_time):
            raise ValueError(f"{attribute.name} must be a unix timestamp but got {reference_time}.")

    def json(self):
        return attr.asdict(self)
