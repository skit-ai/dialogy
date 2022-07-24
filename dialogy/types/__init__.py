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
from dialogy.types.entity.amount_of_money import CurrencyEntity
from dialogy.types.entity.base_entity import BaseEntity, entity_synthesis
from dialogy.types.entity.credit_card_number import CreditCardNumberEntity
from dialogy.types.entity.deserialize import EntityDeserializer
from dialogy.types.entity.duration import DurationEntity
from dialogy.types.entity.keyword import KeywordEntity
from dialogy.types.entity.numerical import NumericalEntity
from dialogy.types.entity.people import PeopleEntity
from dialogy.types.entity.time import TimeEntity
from dialogy.types.entity.time_interval import TimeIntervalEntity
from dialogy.types.intent import Intent
from dialogy.types.plugin import PluginFn
from dialogy.types.signal.signal import Signal
from dialogy.types.slots import Slot
from dialogy.types.utterances import Alternative, Transcript, Utterance
