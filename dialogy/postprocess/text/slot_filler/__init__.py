"""
To handle a single dialog we need a system that can:

1. Classify inputs into categories.
2. Extract tokens of additional significance.
3. Check for associations between the two.

A slot-filler does the third bit. Once an [`Intent`](../../../types/intent/__init__.html) and a set of
[`Entities`](../../../types/entity/__init__.html) are identified, there needs to be an arragement that
tells us if any of the entities are related to an [`Intent`](../../../types/intent/__init__.html).

As per the current design, an [`Intent`](../../../types/intent/__init__.html) can contain `Slots`. A `Slot`
fills an entity of a pre-defined type.

- A `Slot` configured to fill a `TimeEntity` will not fill `LocationEntity`.
- A `Slot` will not fill more than one entity even if the type matches.
"""
