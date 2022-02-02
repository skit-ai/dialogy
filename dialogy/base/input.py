from typing import Optional

import attr

from dialogy.types import Utterance
from dialogy.utils import is_unix_ts, normalize


@attr.frozen
class Input:
    utterance: Utterance = attr.ib(converter=normalize, kw_only=True)
    clf_feature: Optional[str] = attr.ib(
        kw_only=True,
        default=None,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    reference_time: int = attr.ib(
        kw_only=True, validator=lambda _, __, x: is_unix_ts(x)
    )
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
    tracked_slots: Optional[dict] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(dict)),
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

    def json(self):
        return attr.asdict(self)
