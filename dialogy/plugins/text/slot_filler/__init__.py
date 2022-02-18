"""
.. _slot_filler:

To handle a single dialog we need a system that can:

1. Classify inputs into categories.
2. Extract tokens of additional significance.
3. Check for associations between the two.

A slot-filler does the third bit. Once an :ref:`Intent <intent>` and a set of
:ref:`Entity <base_entity>` are identified, there needs to be an arrangement that
tells us if any of these are related to each other.

As per the current design, an :ref:`Intent <intent>` can contain a number of :ref:`Slot <slot>`. A :ref:`Slot <slot>`
fills an entity of a pre-defined type.

- A :ref:`Slot <slot>` configured to fill a :ref:`TimeEntity <time_entity>` will not fill a :ref:`KeywordEntity <KeywordEntity>`.
- A :ref:`Slot <slot>` will not fill more than one entity even if the type matches, unless :code:`fill_multiple` is provided.
"""
