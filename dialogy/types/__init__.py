"""
There are few types of significance for an SLU project

1. :ref:`Intent<intent>`
2. :ref:`Entity<base_entity>`
3. :ref:`Slot<slot>`
4. :ref:`Signal<signal>`

.. warning:: This section is a work in progress.

An :ref:`Intent<intent>` tells us the general meaning of a sentence.
A set :ref:`Entity<base_entity>` are significant tokens that can be acted upon by either
participants within a conversation.

We use :ref:`slots<slot>` within :ref:`intents<intent>` to associate relationship between :ref:`intents<intent>` and
:ref:`entities<base_entity>`. You can consider examples like: Reservation of a air ticket requires:

- destination
- origin
- travel date
- travel time
- travel type (round trip, one-way)
- number of passengers.

So these :ref:`entities<base_entity>` would be filled within their respective :ref:`slots<slot>` already expected by the
reservation :ref:`intents<intent>`.
"""
from dialogy.types.entity import (
    BaseEntity,
    DurationEntity,
    KeywordEntity,
    LocationEntity,
    NumericalEntity,
    PeopleEntity,
    TimeEntity,
    TimeIntervalEntity,
)
from dialogy.types.intent import Intent
from dialogy.types.signal.signal import Signal
