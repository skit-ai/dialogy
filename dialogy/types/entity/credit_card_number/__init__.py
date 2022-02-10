from __future__ import annotations

from typing import Any, Dict, List, Optional

import attr
from this import d

from dialogy import constants as const
from dialogy.types.entity import BaseEntity


@attr.s
class CreditCardNumberEntity(BaseEntity):
    entity_type: Optional[str] = attr.ib(
        repr=False, default="credit-card-number", kw_only=True
    )
    issuer: str = attr.ib(validator=attr.validators.instance_of(str), kw_only=True)
    value: Optional[str] = attr.ib(default=None, kw_only=True)
    values: List[Dict[str, Any]] = attr.ib(
        validator=attr.validators.instance_of(list), kw_only=True
    )

    @classmethod
    def from_duckling(
        cls, d: Dict[str, Any], alternative_index: int
    ) -> CreditCardNumberEntity:
        value = d[const.VALUE][const.VALUE]
        return cls(
            range={const.START: d[const.START], const.END: d[const.END]},
            body=d[const.BODY],
            dim=d[const.DIM],
            alternative_index=alternative_index,
            latent=d[const.LATENT],
            values=[{const.VALUE: value}],
            issuer=d[const.VALUE][const.ISSUER],
        )
