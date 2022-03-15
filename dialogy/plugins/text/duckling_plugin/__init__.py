"""
.. _DucklingPlugin:

We use `Duckling <https://github.com/facebook/duckling>`_ for parsing values like: :code:`date`, :code:`time`,
:code:`numbers`, :code:`currency` etc from natural language. The parser will expect Duckling to be running as an http service, and provide
means to connect from the implementation here. Here's a big example for various duckling entities.

Mother of all examples
----------------------

.. ipython::

    In [1]: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=[
       ...:         "number",
       ...:         "people",
       ...:         "time",
       ...:         "duration",
       ...:         "intersect",
       ...:         "amount-of-money",
       ...:         "credit-card-number",
       ...:     ],
       ...:     # Duckling supports multiple dimensions, by specifying a list, we make sure
       ...:     # we are searching for a match within the expected dimensions only.
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = [
       ...:    "between today 7pm and tomorrow 9pm",
       ...:    "can we get up at 6 am",
       ...:    "we are 7 people",
       ...:    "2 children 1 man 3 girls",
       ...:    "can I come now?",
       ...:    "can I come tomorrow",
       ...:    "how about monday then",
       ...:    "call me on 5th march",
       ...:    "I want 4 pizzas",
       ...:    "2 hours",
       ...:    "can I pay $5 instead?",
       ...:    "my credit card number is 4111111111111111",
       ...:]

    In [5]: %%time
       ...: input_, output = workflow.run(Input(utterances=utterances))

    In [6]: output


Testing
-------

1. Connect to the `Duckling API <https://github.com/facebook/duckling>`_ either via a docker container or a local setup.
2. Boot an IPython session and setup an instance of :ref:`DucklingPlugin <DucklingPlugin>`.

.. code-block:: python
    :linenos:

    from pprint import pprint
    from dialogy.workflow import Workflow
    from dialogy.base import Input
    from dialogy.plugins import DucklingPlugin

    duckling_plugin = DucklingPlugin(
        dest="output.entities",
        dimensions=["people", "time"],
        locale="en_IN",
        timezone="Asia/Kolkata",
        origin/master
    )

    entities = duckling_plugin.parse(["We are 2 children coming tomorrow at 5 pm"])
    pprint(entities)
    # [PeopleEntity(
    #     body='2 children', 
    #     type='value', 
    #     parsers=['DucklingPlugin'], 
    #     score=1.0, 
    #     alternative_index=0,
    #     alternative_indices=[0, 0], 
    #     latent=False, 
    #     value=2, 
    #     origin='value', 
    #     unit='child',
    #     entity_type='people')
    # ,TimeEntity(
    #     body='tomorrow at 5 pm', 
    #     type='value', 
    #     parsers=['DucklingPlugin'], 
    #     score=1.0, 
    #     alternative_index=0, 
    #     alternative_indices=[0],
    #     latent=False, 
    #     value='2022-02-11T17:00:00.000+05:30', origin='value', entity_type='datetime', grain='hour')]

    # To convert these to dicts:

    entity_dicts = [entity.json() for entity in entities]
    pprint(entity_dicts)
    # [{'range': {'start': 7, 'end': 17},
    #     'body': '2 children',
    #     'type': 'value',
    #     'parsers': ['DucklingPlugin'],
    #     'score': 1.0,
    #     'alternative_index': 0,
    #     'value': 2,
    #     'unit': 'child',
    #     'entity_type': 'people'},
    # {'range': {'start': 38, 'end': 54},
    #     'body': 'tomorrow at 5 pm',
    #     'type': 'value',
    #     'parsers': ['DucklingPlugin'],
    #     'score': 1.0,
    #     'alternative_index': 0,
    #     'value': '2022-02-11T17:00:00.000+05:30',
    #     'entity_type': 'datetime',
    #     'grain': 'hour'
    # }]

Guards
------

Like all plugins, the Duckling plugin can be :ref:`guarded <Guards>` by conditions that prevent its execution.
You may need this if you want to save on latency and are sure of not expecting entities in those turns. We will use
the :ref:`mother of all examples <Mother of all examples>` from above to make the point. We will use the :code:`current_state` to tell the plugin
to guard itself in the *"SMALL_TALK"* state.

.. ipython::

    In [1]: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=[
       ...:         "number",
       ...:         "people",
       ...:         "date",
       ...:         "time",
       ...:         "duration",
       ...:         "intersect",
       ...:         "amount-of-money",
       ...:         "credit-card-number",
       ...:     ],
       ...:     guards=[lambda i, o: i.current_state == "SMALL_TALK"]
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = [
       ...:    "between today 7pm and tomorrow 9pm",
       ...:    "can we get up at 6 am",
       ...:    "we are 7 people",
       ...:    "2 children 1 man 3 girls",
       ...:    "can I come now?",
       ...:    "can I come tomorrow",
       ...:    "how about monday then",
       ...:    "call me on 5th march",
       ...:    "I want 4 pizzas",
       ...:    "2 hours",
       ...:    "can I pay $5 instead?",
       ...:    "my credit card number is 4111111111111111",
       ...:]

    In [5]: %%time
       ...: input_, output = workflow.run(Input(utterances=utterances, current_state="SMALL_TALK"))

    In [6]: output

You can notice that the time drops from **ms** to **us** and we produce no entities.

Filtering Date and Time
-----------------------

There are cases where we run into ambiguity in entity resolution. A fun case happens usually with
the Hindi language when someone says *"कल"*. The problem is, *"कल"* could be *"tommorrow"* or *"yesterday"*.

Problem
^^^^^^^

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time"],
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["कल"]

    In [5]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [5]: input_, output = workflow.run(Input(utterances=utterances, locale="hi_IN", reference_time=reference_time))

    In [6]: output

See the two entities? 

- We froze our reference time for 1st Jan 2022 at 12:00:00. 
- We get 31st December 2021
- and 2nd Jan 2022.

This could be decoded using additional context. Let's assume it is a given that dates can only be in future. Say
a flight-booking case.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time"],
       ...:     datetime_filters=DucklingPlugin.FUTURE
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["कल"]

    In [5]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [5]: input_, output = workflow.run(Input(utterances=utterances, locale="hi_IN", reference_time=reference_time))

    In [6]: output

We can use :code:`DucklingPlugin.PAST` for inverse. 

What if the context was within the utterance? Say for payment verification cases, we receive these utterances:

- *"कल ही कर दी थी"* -- *"I have already paid yesterday"*
- *"कल कर दूंगा"* -- *"I will pay tomorrow"*

We can't filter out either future or past values. In these cases, the `intent <Intents>` carries the context
for resolving the entity value. We will look into :ref:`Temporal Intents <Temporal Intents>` for more details.


Temporal Intents
-----------------

Filtering
^^^^^^^^^

There are cases where intents carry a notion of time, repeating an example from above:

#. *"कल ही कर दी थी"* -- *"I have already paid yesterday"*
#. *"कल कर दूंगा"* -- *"I will pay tomorrow"*

While we can't decode the entity value for "कल" in the above utterances, the correct intent prediction is:

#. :code:`already_paid`
#. :code:`pay_later`

If we could use this information, we could resolve the entity value for "कल". We will simulate the output
to contain appropriate intents using the :code:`set` method of :ref:`workflow <Workflow>`.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.types import Intent
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time"],
       ...:     temporal_intents={
       ...:         "already_paid": DucklingPlugin.FUTURE,
       ...:         "pay_later": DucklingPlugin.PAST
       ...:     }
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["कल ही कर दी थी"]
       ...: workflow.set("output.intents", [Intent(name="already_paid", score=1.0)])

    In [5]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)
       ...: input_, output = workflow.run(Input(utterances=utterances, locale="hi_IN", reference_time=reference_time))

    In [6]: output

    In [7]: utterances = ["कल ही कर दी थी"]
       ...: workflow.set("output.intents", [Intent(name="pay_later", score=1.0)])
       ...: input_, output = workflow.run(Input(utterances=utterances, locale="hi_IN", reference_time=reference_time))

    In [6]: output

Casting
^^^^^^^

We can also use temporal intents to cast certain entities. Machines can act on absolute time values but 
natural language often has relative units like *"for 2 hours"*. These produce a duration entity.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["duration", "time"],
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["for 2h"]

    In [5]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [5]: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [6]: output

We understand the duration but we could create an absolute time value using the reference time, but we don't know if duration 
should be added or removed.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.types import Intent
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time", "duration"],
       ...:     timezone="Asia/Kolkata",
       ...:     temporal_intents={
       ...:         "already_paid": DucklingPlugin.FUTURE,
       ...:         "pay_later": DucklingPlugin.PAST
       ...:     }
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)
       ...: utterances = ["for 2h"]

    In [5]: workflow.set("output.intents", [Intent(name="already_paid", score=1.0)])
       ...: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [6]: output

    In [7]: workflow.set("output.intents", [Intent(name="pay_later", score=1.0)])
       ...: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [8]: output

In case we need to always cast duration as a future or a past value we can do:


.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.types import Intent
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time", "duration"],
       ...:     timezone="Asia/Kolkata",
       ...:     temporal_intents={
       ...:         "__any__": DucklingPlugin.FUTURE,
       ...:     }
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: reference_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)
       ...: utterances = ["for 2h"]

    In [5]: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [6]: output

    In [7]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["time", "duration"],
       ...:     timezone="Asia/Kolkata",
       ...:     temporal_intents={
       ...:         "__any__": DucklingPlugin.PAST,
       ...:     }
       ...: )

    In [8]: workflow = Workflow([duckling_plugin])
       ...: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))
       ...: output

Setting Time Range Constraints
------------------------------

Sometimes there are cases where you'd expect the user to say a time between only a particular acceptable range,
if the user says *"कल 12:00 बजे"* or *"tomorrow at 12:00"* at 6pm being the current time, now given our context mostly we know that user meant
12pm here next day and not 12am, so if we say our acceptable time range constraint is >= 7am but <= 11pm,
we can capture the time entity correctly.

Problem
^^^^^^^

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["datetime"],
       ...:     timezone="Asia/Kolkata",
       ...:     locale="hi_IN"
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["कल 12:00 बजे"]
    
    In [5]: reference_dt = datetime(2022, 3, 16, 18, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [6]: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [7]: output

Given that current datetime is *"2022-03-16T18:00:00+05:30"* we can see duckling gives the value as *"2022-03-17T00:00:00+05:30"* but we wanted
to capture *"2022-03-17T12:00:00+05:30"* so for that we can define a time range constraint.

.. ipython::

    In [1]: import pytz
       ...: from datetime import datetime
       ...: from dialogy.workflow import Workflow
       ...: from dialogy.base import Input
       ...: from dialogy.plugins import DucklingPlugin
       ...: from dialogy.utils import dt2timestamp

    In [2]: duckling_plugin = DucklingPlugin(
       ...:     dest="output.entities",
       ...:     dimensions=["datetime"],
       ...:     timezone="Asia/Kolkata",
       ...:     locale="hi_IN",
       ...:     constraints={
       ...:         "time": {
       ...:             "gte": {"hour": 7, "minute": 0},
       ...:             "lte": {"hour": 22, "minute": 59}
       ...:         }
       ...:     }
       ...: )

    In [3]: workflow = Workflow([duckling_plugin])

    In [4]: utterances = ["कल 12:00 बजे"]
    
    In [5]: reference_dt = datetime(2022, 3, 16, 18, 0, 0, tzinfo=pytz.timezone("Asia/Kolkata"))
       ...: reference_time = dt2timestamp(reference_dt)

    In [6]: input_, output = workflow.run(Input(utterances=utterances, reference_time=reference_time))

    In [7]: output

Now we can see that it gives the correct entity value i.e *"2022-03-17T12:00:00+05:30"*

"""
import json
import operator
import traceback
from concurrent import futures
from datetime import datetime
from pprint import pformat
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import pydash as py_
import pytz
import requests
from pytz.tzinfo import BaseTzInfo
from tqdm import tqdm

from dialogy import constants as const
from dialogy.base import Guard, Input, Output, Plugin
from dialogy.base.entity_extractor import EntityScoringMixin
from dialogy.types import BaseEntity, Intent
from dialogy.types.entity.deserialize import EntityDeserializer
from dialogy.utils import dt2timestamp, lang_detect_from_text, logger


class DucklingPlugin(EntityScoringMixin, Plugin):
    """
    :param dimensions: `Dimensions <https://github.com/facebook/duckling#supported-dimensions>`_. Of the listed
    dimensions, we support:

        - `Numeral`
        - `Time`
        - `TimeInterval`
        - `Duration`
        - `People` - This isn't part of the standard, we have a private fork to support this.

        Do note, passing more dimensions is not free. Duckling would search for extra set of patterns just because
        those dimensions were expected.
    :type dimensions: Optional[List[str]]

    :param locale: The format for expressing locale requires language code and country name ids. Read about
        `sections <https://github.com/facebook/duckling#extending-duckling>`_ that define
        `ISO-639-codes <https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes>`_ for languages and
        `ISO3166 alpha2 country code <https://www.iso.org/obp/ui/#search/code/>`_ for country codes.
        Examples: `"en_IN"`, `"en_US"`, `"en_GB"`.
    :type locale: str

    :param timezone: `pytz` Timezone. This is especially important when services are deployed across different
    geographies and consistency is expected in the responses. Get a valid value from a `list of tz database timezones
    <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_. Example: `"Asia/Kolkata"` :type timezone:
    Optional[str]

    :param timeout: There are certain strings which tend to stall Duckling:
    `example <https://github.com/facebook/duckling/issues/338>`_.
    In such cases, to prevent the overall experience to slow
    down as well, provide a certain timeout value, defaults to 0.5.
    :type timeout: float

    :param url: The address where Duckling's entity parser can be reached, defaults to "http://0.0.0.0:8000/parse".
    :type url: Optional[str]
    """

    FUTURE = const.FUTURE
    """
    Select time entity values with scores greater than or equal to the reference time.
    """

    PAST = const.PAST
    """
    Select time entity values with scores lesser than or equal to the reference time.
    """

    __DATETIME_OPERATION_ALIAS = {FUTURE: operator.ge, PAST: operator.le}

    def __init__(
        self,
        dimensions: List[str],
        timezone: str = "UTC",
        timeout: float = 0.5,
        url: str = "http://0.0.0.0:8000/parse",
        locale: str = "en_IN",
        constraints: Optional[Dict[str, Any]] = None,
        temporal_intents: Optional[Dict[str, str]] = None,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        datetime_filters: Optional[str] = None,
        threshold: Optional[float] = None,
        activate_latent_entities: Union[Callable[..., bool], bool] = False,
        reference_time_column: str = const.REFERENCE_TIME,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        debug: bool = False,
    ) -> None:
        """
        constructor
        """
        super().__init__(
            dest=dest,
            guards=guards,
            debug=debug,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
        )
        self.dimensions = dimensions
        self.locale = locale
        self.timezone = timezone
        self.timeout = timeout
        self.threshold = threshold
        self.url = url
        self.temporal_intents = temporal_intents or {}
        self.reference_time: Optional[int] = None
        self.reference_time_column = reference_time_column
        self.datetime_filters = datetime_filters
        self.activate_latent_entities = activate_latent_entities
        self.constraints = constraints
        self.session = requests.Session()
        self.session.mount(
            "http://",
            requests.adapters.HTTPAdapter(
                max_retries=1, pool_maxsize=10, pool_block=True
            ),
        )
        self.headers: Dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }

    def __set_timezone(self) -> Optional[BaseTzInfo]:
        """
        Set timezone as BaseTzInfo from compatible timezone string.

        Raises:
            pytz.UnknownTimeZoneError:

        :raises pytz.UnknownTimeZoneError: If `self.timezone` is not in `list of tz database
            timezones <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`_.
        :return: A valid timezone
        :rtype: Optional[BaseTzInfo]
        """
        # If timezone is an unsafe string, we will handle a `pytz.UnknownTimeZoneError` exception
        # and pass a friendly message.
        try:
            return pytz.timezone(self.timezone)
        except pytz.UnknownTimeZoneError as unknown_timezone_error:
            raise pytz.UnknownTimeZoneError(
                f"The timezone {self.timezone} is invalid"
                " check valid types here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
            ) from unknown_timezone_error

    def __create_req_body(
        self,
        text: str,
        reference_time: Optional[int] = None,
        locale: str = "en_IN",
        use_latent: Union[Callable[..., bool], bool] = False,
    ) -> Dict[str, Any]:
        """
        create request body for entity parsing

        example: "3 people tomorrow"

        Make your own reference time using the current timestamp using: :code:`int(datetime.now().timestamp() * 1000)`
        These are the milliseconds since the `Unix epoch <https://en.wikipedia.org/wiki/Unix_time>`_

        :param text: A sentence or document.
        :type text: str
        :param reference_time: Impart context of timestamp,
        relevant for time related entities. Resolve relative time like "yesterday", "next month", etc.
        :type Optional[int]
        :param reference_time: Optional[int]
        :return: request object for Duckling API.
        :rtype: Dict[str, Any]
        """
        dimensions = self.dimensions
        activate_latent_entities = use_latent

        activate_latent_entities = (
            activate_latent_entities
            if isinstance(activate_latent_entities, bool)
            else activate_latent_entities()
        )

        payload = {
            "text": text,
            "locale": locale or self.locale,
            "tz": self.__set_timezone(),
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
            "latent": activate_latent_entities,
        }
        logger.debug("Duckling API payload:")
        logger.debug(pformat(payload))

        return payload

    def get_operator(self, filter_type: Any) -> Any:
        try:
            return getattr(operator, filter_type)
        except (AttributeError, TypeError) as exception:
            logger.debug(traceback.format_exc())
            raise ValueError(
                f"Expected datetime_filters to be one of {self.FUTURE}, {self.PAST} "
                "or a valid comparison operator here: https://docs.python.org/3/library/operator.html"
            ) from exception

    def select_datetime(
        self, entities: List[BaseEntity], filter_type: Any
    ) -> List[BaseEntity]:
        """
        Select datetime entities as per the filters provided in the configuration.

        :param entities: A list of entities.
        :type entities: List[BaseEntity]
        :param filter_type:
        :type filter_type: str
        :return: List of entities obtained after applying comparator functions.
        :rtype: List[BaseEntity]
        """
        if not isinstance(filter_type, str):
            raise TypeError(
                f"Expected datetime_filters to be a str and one of {self.FUTURE}, {self.PAST} or"
                " a valid comparison operator here: https://docs.python.org/3/library/operator.html"
            )

        if filter_type in self.__DATETIME_OPERATION_ALIAS:
            operation = self.__DATETIME_OPERATION_ALIAS[filter_type]
        else:
            operation = self.get_operator(filter_type)

        if not self.reference_time:
            return entities  # pragma: no cover

        time_entities, other_entities = py_.partition(
            entities, lambda entity: entity.dim == const.TIME
        )

        filtered_time_entities = [
            entity
            for entity in time_entities
            if operation(dt2timestamp(entity.get_value()), self.reference_time)
        ]
        return filtered_time_entities + other_entities

    def apply_filters(self, entities: List[BaseEntity]) -> List[BaseEntity]:
        """
        Conditionally remove entities.

        The utility of this method is tracked here:
        https://github.com/Vernacular-ai/dialogy/issues/42

        We needed a way to express, not all datetime entities are needed. There are needs which can be
        expressed as filters: want greater or lesser than the reference time, etc. There are more applications
        where we expect sorting, filtering by other attributes as well. This method is an advent of such expressions.

        :param entities: A list of entities.
        :type entities: List[BaseEntity]
        :return: A list of entities obtained after applying filters.
        :rtype: List[BaseEntity]
        """
        if self.datetime_filters:
            return self.select_datetime(entities, self.datetime_filters)

        # We call the filters that exist on the EntityExtractor class like threshold filtering.
        return super().apply_filters(entities)

    def _reshape(
        self,
        entities_json: List[Dict[str, Any]],
        alternative_index: int = 0,
        reference_time: Optional[int] = None,
        duration_cast_operator: Optional[str] = None,
    ) -> List[BaseEntity]:
        """
        Create a list of :ref:`BaseEntity <base_entity>` objects from a list of entity dicts.

        :param entities_json: List of entities derived from Duckling's API.
        :type entities_json: List[Dict[str, Any]]
        :raises NotImplementedError: Raised when dimensions not supported by the project are used.
        :raises KeyError: Expected keys in entity dict don't match the Entity class.
        :return: A list of objects subclassed from :ref:`BaseEntity <base_entity>`
        :rtype: Optional[List[BaseEntity]]
        """
        deserialized_entities = []
        for entity_json in entities_json:
            entity = EntityDeserializer.deserialize_duckling(
                entity_json,
                alternative_index,
                reference_time=reference_time,
                timezone=self.timezone,
                duration_cast_operator=duration_cast_operator,
                constraints=self.constraints,
            )
            entity.add_parser(self)
            deserialized_entities.append(entity)
        return deserialized_entities

    def _get_entities(
        self,
        text: str,
        locale: str = "en_IN",
        reference_time: Optional[int] = None,
        use_latent: Union[Callable[..., bool], bool] = False,
        sort_idx: int = 0,
    ) -> Dict[str, Any]:
        """
        Get entities from duckling-server.

        Assuming duckling-server is running at expected `url`. The entities are returned in
        `json` compatible format.

        :param text: The sentence or document in which entities must be looked up.
        :type text: str
        :param reference_time: Cases where relative units of time are mentioned,
                                like "today", "now", etc. We need to know the current time
                                to parse the values into usable dates/times, defaults to None
        :type reference_time: Optional[int], optional
        :raises ValueError: Duckling API call failure leading to no json response.
        :return: Duckling entities as :code:`dicts`.
        :rtype: List[Dict[str, Any]]
        """
        body = self.__create_req_body(
            text, reference_time=reference_time, locale=locale, use_latent=use_latent
        )

        try:
            response = self.session.post(
                self.url, data=body, headers=self.headers, timeout=self.timeout
            )

            if response.status_code == 200:
                # The API call was successful, expect the following to contain entities.
                # A list of dicts or an empty list.
                return {const.IDX: sort_idx, const.VALUE: response.json()}
        except requests.exceptions.Timeout as timeout_exception:
            logger.error(f"Duckling timed out: {timeout_exception}")  # pragma: no cover
            logger.error(pformat(body))  # pragma: no cover
            return {const.IDX: sort_idx, const.VALUE: []}  # pragma: no cover
        except requests.exceptions.ConnectionError as connection_error:
            logger.error(f"Duckling server is turned off?: {connection_error}")
            logger.error(pformat(body))
            raise requests.exceptions.ConnectionError from connection_error

        # Control flow reaching here would mean the API call wasn't successful.
        # To prevent rest of the things from crashing, we will raise an exception.
        raise ValueError(
            f"Duckling API call failed | [{response.status_code}]: {response.text}"
        )

    def _get_entities_concurrent(
        self,
        texts: List[str],
        locale: str = "en_IN",
        reference_time: Optional[int] = None,
        use_latent: Union[Callable[..., bool], bool] = False,
    ) -> List[List[Dict[str, Any]]]:
        """
        Make multiple-parallel API calls to duckling-server .

        :param texts: A list of strings to be parsed concurrently via duckling.
        :type texts: List[str]
        :param locale: Defined in __init__, defaults to "en_IN"
        :type locale: str, optional
        :param reference_time: Cases where relative units of time are mentioned,
                                like "today", "now", etc. We need to know the current time
                                to parse the values into usable dates/times, defaults to None
        :type reference_time: Optional[int], optional
        :param use_latent: True returns latent entities, defaults to False
        :type use_latent: bool, optional
        :return: Duckling entities as :code:`dicts`.
        :rtype: List[List[Dict[str, Any]]]
        """
        workers = min(10, max(len(texts), 1))
        with futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures_ = [
                executor.submit(
                    self._get_entities,
                    text,
                    locale,
                    reference_time=reference_time,
                    use_latent=use_latent,
                    sort_idx=i,
                )
                for i, text in enumerate(texts)
            ]
        entities_list = [future.result() for future in futures.as_completed(futures_)]
        return [
            entities[const.VALUE]
            for entities in sorted(
                entities_list, key=lambda entities: entities[const.IDX]
            )
        ]

    def apply_entity_classes(
        self,
        list_of_entities: List[List[Dict[str, Any]]],
        reference_time: Optional[int] = None,
        timezone: str = "UTC",
        duration_cast_operator: Optional[str] = None,
    ) -> List[BaseEntity]:
        shaped_entities = []
        for (alternative_index, entities) in enumerate(list_of_entities):
            shaped_entities.append(
                self._reshape(
                    entities,
                    alternative_index=alternative_index,
                    reference_time=reference_time,
                    duration_cast_operator=duration_cast_operator,
                )
            )
        return py_.flatten(shaped_entities)

    def validate(
        self, input_: Union[str, List[str]], reference_time: Optional[int]
    ) -> "DucklingPlugin":
        input_is_str = isinstance(input_, str)
        inputs_are_list_of_strings = isinstance(input_, list) and all(
            isinstance(text, str) for text in input_
        )
        if not isinstance(reference_time, int) and self.datetime_filters:
            raise TypeError(
                "Duckling requires reference_time to be a unix timestamp (int) but"
                f" {type(reference_time)} was found"
                "https://stackoverflow.com/questions/20822821/what-is-a-unix-timestamp-and-why-use-it\n"
            )

        if not input_is_str and not inputs_are_list_of_strings:
            raise TypeError(f"Expected {input_} to be a List[str] or str.")
        return self

    def parse(
        self,
        transcripts: Union[str, List[str]],
        locale: Optional[str] = None,
        reference_time: Optional[int] = None,
        use_latent: Union[Callable[..., bool], bool] = False,
        intents: Optional[List[Intent]] = None,
    ) -> List[BaseEntity]:
        list_of_entities: List[List[Dict[str, Any]]] = []
        entities: List[BaseEntity] = []
        duration_cast_operator = None
        intent = None

        if intents:
            intent, *_ = intents

        if isinstance(intent, Intent) and intent.name in self.temporal_intents:
            duration_cast_operator = self.datetime_filters = self.temporal_intents.get(
                intent.name
            )

        if const.ANY in self.temporal_intents:
            duration_cast_operator = self.temporal_intents.get(const.ANY)

        locale = locale or self.locale
        self.reference_time = reference_time = reference_time or self.reference_time
        self.validate(transcripts, reference_time)
        if isinstance(transcripts, str):
            transcripts = [transcripts]  # pragma: no cover

        list_of_entities = self._get_entities_concurrent(
            transcripts,
            locale=locale,
            reference_time=reference_time,
            use_latent=use_latent,
        )
        entities = self.apply_entity_classes(
            list_of_entities,
            reference_time,
            duration_cast_operator=duration_cast_operator,
        )
        entities = self.entity_consensus(entities, len(transcripts))
        return self.apply_filters(entities)

    def utility(self, input: Input, output: Output) -> List[BaseEntity]:
        """
        Produces Duckling entities, runs with a :ref:`Workflow's run<workflow_run>` method.

        :param argbrightons: Expects a tuple of :code:`Tuple[natural language for parsing entities, reference time in milliseconds, locale]`
        :type args: Tuple(Union[str, List[str]], int, str)
        :return: A list of duckling entities.
        :rtype: List[BaseEntity]
        """
        transcripts = input.transcripts
        self.reference_time = input.reference_time
        self.locale = input.locale or self.locale
        use_latent = input.latent_entities

        return self.parse(
            transcripts,
            locale=self.locale,
            reference_time=self.reference_time,
            use_latent=use_latent,
            intents=output.intents,
        )

    def transform(self, training_data: pd.DataFrame) -> pd.DataFrame:
        """
        Transform training data.

        :param training_data: Training data.
        :type training_data: pd.DataFrame
        :return: Transformed training data.
        :rtype: pd.DataFrame
        """
        if not self.use_transform:
            return training_data

        logger.debug(f"Transforming dataset via {self.__class__.__name__}")
        logger.disable("dialogy")
        training_data = training_data.copy()
        if self.output_column not in training_data.columns:
            training_data[self.output_column] = None

        for i, row in tqdm(training_data.iterrows(), total=len(training_data)):
            reference_time = row[self.reference_time_column]
            if isinstance(reference_time, str):
                reference_time = int(
                    datetime.fromisoformat(reference_time).timestamp() * 1000
                )
            elif pd.isna(reference_time):
                continue
            elif not isinstance(reference_time, int):
                raise TypeError(
                    f"{reference_time=} should be isoformat date or unix timestamp integer."
                )
            transcripts = self.make_transform_values(row[self.input_column])
            entities = self.parse(
                transcripts,
                lang_detect_from_text(self.input_column),
                reference_time=reference_time,
                use_latent=self.activate_latent_entities,
            )
            if row[self.output_column] is None or pd.isnull(row[self.output_column]):
                training_data.at[i, self.output_column] = entities
            else:
                training_data.at[i, self.output_column] = (
                    row[self.output_column] + entities
                )
        logger.enable("dialogy")
        return training_data
