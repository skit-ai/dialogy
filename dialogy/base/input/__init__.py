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

from typing import Any, Dict, List, Optional

import attr

from dialogy.types import Utterance
from dialogy.utils import is_unix_ts, normalize


@attr.frozen
class Input:
    """
    Represents the inputs of the SLU API.
    """

    utterances: List[Utterance] = attr.ib(kw_only=True)
    """
    ASRs produce utterances. 
    Each utterance contains N-hypothesis. 
    Each hypothesis is a :code:`dict` with keys :code:`"transcript"` and :code:`"confidence"`.
    """

    reference_time: Optional[int] = attr.ib(default=None, kw_only=True)
    """
    The time that should be used for parsing relative time values.
    This is a Unix timestamp in seconds.
    utils/datetime.py has :ref:`make_unix_ts <make_unix_ts>` to help convert 
    a date in ISO 8601 format to unix ms timestamp.
    """

    latent_entities: bool = attr.ib(default=False, kw_only=True, converter=bool)
    """
    A switch to turn on/off production of latent entities via Duckling API
    If you need to parse "4" as 4 am or 4 pm. Note the absence of "am" or "pm" in the utterance.
    Then you might need this to be set as :code:`True`.
    It may be helpful to keep it :code:`False` unless clearly required. 
    """

    transcripts: List[str] = attr.ib(default=None)
    """
    A derived attribute. We cross product each utterance and return a list of strings.
    We use this to :ref:`normalize <normalize>` utterances.
    """

    clf_feature: Optional[List[str]] = attr.ib(  # type: ignore
        kw_only=True,
        factory=list,
        validator=attr.validators.optional(attr.validators.instance_of(list)),
    )
    """
    Placeholder for the features of an intent classifier.
    
    .. code-block:: python

        ["<s> I want to book a flight </s> <s> I want to book flights </s> <s> I want to book a flight to Paris </s>"]
    """

    lang: str = attr.ib(
        default="en", kw_only=True, validator=attr.validators.instance_of(str)
    )
    """
    Expected language of the input. This is needed for language dependent plugins.
    These are present in https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    for "English" the code is "en". 
    """

    locale: str = attr.ib(
        default="en_IN",
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),  # type: ignore
    )
    """
    The locale identifier consists of at least a language code and a country/region code.
    We keep "en_IN" as our default. This is used by Duckling for parsing patterns as per the 
    locale. If locale is missing i.e. None, we may fallback to :code:`lang` instead.
    """

    timezone: str = attr.ib(
        default="UTC",
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),  # type: ignore
    )
    """
    Timezones from https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    Used by duckling or any other date/time parsing plugins.
    """

    slot_tracker: Optional[List[Dict[str, Any]]] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(list)),
    )
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

    current_state: Optional[str] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    """
    Points at the active state (or node) within the conversation graph.
    """

    previous_intent: Optional[str] = attr.ib(
        default=None,
        kw_only=True,
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    """
    The name of the intent that was predicted by the classifier in (exactly) the previous turn.
    """
    history: Optional[List[Dict[str, Any]]] = attr.ib(default=None, kw_only=True)

    def __attrs_post_init__(self) -> None:
        try:
            object.__setattr__(self, "transcripts", normalize(self.utterances))
        except TypeError:
            ...

    @reference_time.validator  # type: ignore
    def _check_reference_time(
        self, attribute: attr.Attribute, reference_time: Optional[int]  # type: ignore
    ) -> None:
        if reference_time is None:
            return
        if not isinstance(reference_time, int):
            raise TypeError(f"{attribute.name} must be an integer.")
        if not is_unix_ts(reference_time):
            raise ValueError(
                f"{attribute.name} must be a unix timestamp but got {reference_time}."
            )

    def json(self) -> Dict[str, Any]:
        """
        Serialize `Input`_ to a JSON-like dict.

        :return: A dictionary that represents an `Input`_ instance.
        :rtype: Dict[str, Any]
        """
        return attr.asdict(self)

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
            return attr.evolve(reference, **d)
        return attr.evolve(cls(utterances=d["utterances"]), **d)  # type: ignore
