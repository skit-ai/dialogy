"""
.. _duckling_plugin:

This module exposes a parser for `Duckling <https://github.com/facebook/duckling>`_.

`Duckling <https://github.com/facebook/duckling>`_ helps parsing values like: :code:`date`, :code:`time`,
:code:`numbers`, :code:`currency` etc. The parser will expect Duckling to be running as an http service, and provide
means to connect from the implementation here.

.. code-block:: python
    :linenos:

    from pprint import pprint
    from dialogy.workflow import Workflow
    from dialogy.base import Input
    from dialogy.plugins import DucklingPlugin

    duckling_plugin = DucklingPlugin(
        dest="output.entities",
        dimensions=["people"],
        # Duckling supports multiple dimensions, by specifying a list, we make sure
        # we are searching for a match within the expected dimensions only.
        locale="en_IN",
        # Duckling supports a set of locales, we need to provide this info to
        # get language specific matches.
        timezone="Asia/Kolkata",
        # Date/Time related entities make this field imperative.
    )

    workflow = Workflow([duckling_plugin])
    input_, output = workflow.run(Input(utterances=[[{"transcript": "there are 7 people"}]]))

    pprint(input_)
    # {'clf_feature': [],
    #  'current_state': None,
    #  'lang': 'en',
    #  'latent_entities': False,
    #  'locale': 'en_IN',
    #  'previous_intent': None,
    #  'reference_time': None,
    #  'slot_tracker': None,
    #  'timezone': 'UTC',
    #  'transcripts': ['there are 7 people'],
    #  'utterances': [[{'transcript': 'there are 7 people'}]]}

    pprint(output)
    # {'entities': [{'alternative_index': 0,
    #                'body': '7 people',
    #                'entity_type': 'people',
    #                'parsers': ['DucklingPlugin'],
    #                'range': {'end': 18, 'start': 10},
    #                'score': 1.0,
    #                'type': 'value',
    #                'unit': '',
    #                'value': 7}],
    #  'intents': []}

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
    )

    entities = duckling_plugin.parse(["We are 2 children coming tomorrow at 5 pm"])
    print(entities)
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
    print(entity_dicts)
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
from dialogy.types import BaseEntity
from dialogy.types.entity.deserialize import deserialize_duckling_entity
from dialogy.utils import dt2timestamp, lang_detect_from_text, logger


class DucklingPlugin(EntityScoringMixin, Plugin):
    """
    A :ref:`Plugin<plugin>` for extracting entities using `Duckling <https://github.com/facebook/duckling>`_. Once
    instantiated, a :code:`duckling_parser` object will interface to an http server, running `Duckling
    <https://github.com/facebook/duckling>`_.

    .. _DucklingPlugin:

    This object when used as a plugin, transforms the :code:`List[Dict[str, Any]]` returned from the API to a
    :ref:`BaseEntity<base_entity>` or one of its subclasses.

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

    FUTURE = "future"
    """
    This selects entity values with scores greater than or equal to the threshold.
    """

    PAST = "past"
    """
    This selects entity values with scores less than or equal to the threshold.
    """

    __DATETIME_OPERATION_ALIAS = {FUTURE: operator.ge, PAST: operator.le}

    def __init__(
        self,
        dimensions: List[str],
        timezone: str,
        timeout: float = 0.5,
        url: str = "http://0.0.0.0:8000/parse",
        locale: str = "en_IN",
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
        self.reference_time: Optional[int] = None
        self.reference_time_column = reference_time_column
        self.datetime_filters = datetime_filters
        self.activate_latent_entities = activate_latent_entities
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
        self.activate_latent_entities = use_latent or self.activate_latent_entities
        activate_latent_entities = (
            self.activate_latent_entities
            if isinstance(self.activate_latent_entities, bool)
            else self.activate_latent_entities()
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
            entity = deserialize_duckling_entity(entity_json, alternative_index)
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
            return {const.IDX: sort_idx, const.VALUE: []}

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
    ) -> List[BaseEntity]:
        shaped_entities = []
        for (alternative_index, entities) in enumerate(list_of_entities):
            shaped_entities.append(
                self._reshape(entities, alternative_index, reference_time)
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
    ) -> List[BaseEntity]:
        list_of_entities: List[List[Dict[str, Any]]] = []
        entities: List[BaseEntity] = []

        locale = locale or self.locale
        reference_time = reference_time or self.reference_time

        self.validate(transcripts, reference_time)
        if isinstance(transcripts, str):
            transcripts = [transcripts]  # pragma: no cover

        try:
            list_of_entities = self._get_entities_concurrent(
                transcripts,
                locale,
                reference_time=reference_time,
                use_latent=use_latent,
            )
            entities = self.apply_entity_classes(list_of_entities, reference_time)
            entities = self.entity_consensus(entities, len(transcripts))
            return self.apply_filters(entities)
        except ValueError as value_error:
            raise ValueError(str(value_error)) from value_error

    def utility(self, input: Input, _: Output) -> List[BaseEntity]:
        """
        Produces Duckling entities, runs with a :ref:`Workflow's run<workflow_run>` method.

        :param args: Expects a tuple of :code:`Tuple[natural language for parsing entities, reference time in milliseconds, locale]`
        :type args: Tuple(Union[str, List[str]], int, str)
        :return: A list of duckling entities.
        :rtype: List[BaseEntity]
        """
        transcripts = input.transcripts
        reference_time = input.reference_time
        locale = input.locale
        use_latent = input.latent_entities
        return self.parse(
            transcripts, locale, reference_time=reference_time, use_latent=use_latent
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
