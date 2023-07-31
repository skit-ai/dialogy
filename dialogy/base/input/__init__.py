"""
.. _Input:

The :ref:`Input <Input>` class creates immutable instances that describe the inputs of a single turn of a conversation.
There are some attributes that may have aggregations of previous turns like the :code:`slot_tracker` or entire :code:`history`.

.. admonition:: Why do I see :ref:`Input <Input>` and :ref:`Output <Output>` as inputs to all :ref:`Plugins <AbstractPlugin>`?

    It is a common pattern for all the plugins to require both as arguments. Since this could be confusing nomenclature, :ref:`Input <Input>`
    and :ref:`Output <Output>` bear meaning and even separation for the SLU API, **not for** :ref:`Plugins <AbstractPlugin>`.


Updates
-------

While writing plugins, we would need to update the attributes of :ref:`Input <Input>`, the following **doesn't** work!

.. ipython::

    In [1]: from dialogy.base import Input
       ...: from dialogy.utils import make_unix_ts

    In [2]: # Check the attributes in the object logged below. 
       ...: input_x = Input(utterances="hello world", lang="hi", timezone="Asia/Kolkata")

    In [3]: input_x

Issues with Frozen Instance Update
##################################

Now if we try the following:

.. ipython::
    :okexcept:

    In [4]: input_x.utterances = "hello"

We can see re-assigning values to attributes isn't allowed. 

Updating a frozen instance
##########################

We have to create new instances, but we have some syntax for it: 

.. ipython::

    In [1]: input_x = Input(utterances="hello world", lang="hi", timezone="Asia/Kolkata")

    In [2]: input_y = Input.from_dict({"utterances": "hello"})

    In [3]: input_y

but by doing this, we lost the :code:`lang` and :code:`timezone` attributes to system defaults.

Reusing an existing instance
############################

We can re-use an existing instance to create a new.
This way, we don't have to write every existing property on a previous :ref:`Input <Input>`.

.. ipython::

    In [1]: input_x = Input(utterances="hello world", lang="hi", timezone="Asia/Kolkata")

    In [2]: input_y = Input.from_dict({"utterances": "hello"}, reference=input_x)

    In [3]: input_y

Serialization
-------------

If there is a need to represent an :ref:`Input<Input>` as a `dict` we can do the following:

.. ipython::

    In [4]: input_y.json()

"""
from __future__ import annotations

from functools import reduce
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from dialogy.types import Utterance
from dialogy.utils import normalize, get_best_transcript, is_unix_ts


class Input(BaseModel):
    """
    Represents the inputs of the SLU API.
    """

    utterances: List[Utterance]
    """
    ASRs produce utterances. 
    Each utterance contains N-hypothesis. 
    Each hypothesis is a :code:`dict` with keys :code:`"transcript"` and :code:`"confidence"`.
    """

    reference_time: Optional[int] = None
    """
    The time that should be used for parsing relative time values.
    This is a Unix timestamp in seconds.
    utils/datetime.py has :ref:`make_unix_ts <make_unix_ts>` to help convert 
    a date in ISO 8601 format to unix ms timestamp.
    """

    latent_entities: bool = False
    """
    A switch to turn on/off production of latent entities via Duckling API
    If you need to parse "4" as 4 am or 4 pm. Note the absence of "am" or "pm" in the utterance.
    Then you might need this to be set as :code:`True`.
    It may be helpful to keep it :code:`False` unless clearly required. 
    """

    transcripts: List[str] = None  # type: ignore
    """
    A derived attribute. We cross product each utterance and return a list of strings.
    We use this to :ref:`normalize <normalize>` utterances.
    """

    best_transcript: str = None  # type: ignore
    """
    A derived attribute. Contains the best alternative selected out of the utterances.
    """

    clf_feature: Optional[List[str]] = Field(default_factory=list)
    """
    Placeholder for the features of an intent classifier.
    
    .. code-block:: python
        ["<s> I want to book a flight </s> <s> I want to book flights </s> <s> I want to book a flight to Paris </s>"]
    """

    lang: str = "en"
    """
    Expected language of the input. This is needed for language dependent plugins.
    These are present in https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    for "English" the code is "en". 
    """

    locale: str = "en_IN"
    """
    The locale identifier consists of at least a language code and a country/region code.
    We keep "en_IN" as our default. This is used by Duckling for parsing patterns as per the 
    locale. If locale is missing i.e. None, we may fallback to :code:`lang` instead.
    """

    timezone: str = "UTC"
    """
    Timezones from https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    Used by duckling or any other date/time parsing plugins.
    """

    slot_tracker: Optional[List[Dict[str, Any]]] = None
    """
    This data structure tracks the slots that were filled in previous turns.
    This may come handy if we want to filter or reduce entities depending on our history.
    We use this in our :ref:`CombineDateTimeOverSlots <CombineDateTimeOverSlots>` plugin.

    .. code-block:: python
    
        [{
            "name": "_callback_",               # the intent name
            "slots": [{
                "name": "callback_datetime",    # the slot name
                "type": [                       # can fill entities of these types.
                    "time",
                    "date",
                    "datetime"
                ],
                "values": [{                    # entities that were filled previously
                    "alternative_index": 0,
                    "body": "tomorrow",
                    "entity_type": "date",
                    "grain": "day",
                    "parsers": ["duckling"],
                    "range": {
                        "end": 8,
                        "start": 0
                    },
                    "score": None,
                    "type": "value",
                    "value": "2021-10-15T00:00:00+05:30"
                }]
            }]
        }]
    """

    current_state: Optional[str] = None
    """
    Points at the active state (or node) within the conversation graph.
    """

    nls_label: Optional[str] = None
    """
    Points at the NLS Label of the active (current) node within the conversation graph.
    """

    expected_slots: List[str] = Field(default_factory=list)
    """
    In a given turn, the expected number of slots to fill.
    """

    previous_intent: Optional[str] = None
    """
    The name of the intent that was predicted by the classifier in (exactly) the previous turn.
    """
    history: Optional[List[Dict[str, Any]]] = None

    class Config:
        allow_mutation = False

    def __init__(self, **data):  # type: ignore
        if "utterances" in data:
            data["transcripts"] = normalize(data["utterances"])
            data["best_transcript"] = get_best_transcript(data["transcripts"])
        data["expected_slots"] = list(set(data.get("expected_slots", [])))

        defaults = {
            "latent_entities": False,
            "lang": "en",
            "locale": "en_IN",
            "timezone": "UTC",
        }

        # validator for `reference_time` before int type casting
        if "reference_time" in data and data["reference_time"] is not None:
            if not isinstance(data["reference_time"], int):
                raise TypeError(
                    f"`reference_time` should be int but got: {data['reference_time']}"
                )

        for k, d in defaults.items():
            data[k] = data.get(k, d) or d

        super().__init__(**data)

    @validator("reference_time")
    def check_reference_time(cls, v):  # type: ignore
        if not v:
            return None
        if not is_unix_ts(v):
            raise ValueError(f"`reference_time` must be a unix timestamp but got {v}.")
        return v

    @classmethod
    def from_dict(cls, d: Dict[str, Any], reference: Optional[Input] = None) -> Input:
        """
        Create a new `Input`_ instance from a dictionary.

        :param d: A dictionary such that keys are a subset of `Input`_ attributes.
        :type d: Dict[str, Any]
        :param reference: An existing `Input`_ instance., defaults to None
        :type reference: Optional[Input], optional
        :return: A new `Input`_ instance.
        :rtype: Input
        """
        if reference:
            return reference.copy(update=d, deep=True)
        return cls(**d)

    def find_entities_in_history(
        self,
        intent_names: Optional[List[str]] = None,
        slot_names: Optional[List[str]] = None,
    ) -> Union[List[Dict[str, Any]], None]:
        if not self.history:
            return None

        _intent_names: List[str] = intent_names or []
        _slot_names: List[str] = slot_names or []

        # Flatten the history to a list of intents
        intents: List[Dict[str, Any]] = reduce(
            lambda intents, res: intents + res["intents"], self.history[::-1], []
        )

        # Filter intents by name
        required_intents = filter(
            lambda intent: intent["name"] in _intent_names, intents
        )

        # Flatten the intents to a list of slots
        slots: List[Dict[str, Any]] = reduce(
            lambda slots, intent: slots + intent["slots"], required_intents, []
        )

        # Filter slots by name
        required_slots = filter(lambda slot: slot["name"] in _slot_names, slots)

        return list(
            reduce(lambda entities, slot: entities + slot["values"], required_slots, [])
        )
