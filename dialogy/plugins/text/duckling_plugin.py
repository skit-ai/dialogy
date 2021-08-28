"""
.. _duckling_plugin:

This module exposes a parser for `Duckling <https://github.com/facebook/duckling>`_.

`Duckling <https://github.com/facebook/duckling>`_ helps parsing values like: :code:`date`, :code:`time`,
:code:`numbers`, :code:`currency` etc. The parser will expect Duckling to be running as an http service, and provide
means to connect from the implementation here.

.. code-block:: python
    :linenos:
    :emphasize-lines: 4, 30

    from dialogy.workflow import Workflow

    def update_workflow(workflow, entities):
        workflow.input["duckling_entities"] = entities

    duckling_plugin = DucklingPlugin(
        access=lambda workflow: (workflow.input["sentence"], workflow.input["reftime"], workflow.input["locale"])
        # the access method guides the plugin to data within a workflow.
        # in this case, the `input` property of a workflow is expected
        # to be a `dict` with a key named "sentence". Check line 30.
        mutate=update_workflow,
        # the mutate method guides the plugin to place the processed output
        # somewhere on the workflow.
        dimensions=["people"],
        # Duckling supports multiple dimensions, by specifying a list, we make sure
        # we are searching for a match within the expected dimensions only.
        locale="en_IN",
        # Duckling supports a set of locales, we need to provide this info to
        # get language specific matches.
        timezone="Asia/Kolkata",
        # Date/Time related entities make this field imperative.
    )() # ⬅️ the instance is also getting called.
    # Notice that we instantiate the class and also
    # invoke __call__ method of the instance.
    # The returned value from the instance is the plugin.
    #
    # This is a standard pattern across all plugins.

    workflow = Workflow(preprocessors=[duckling_plugin])
    workflow.run(input_={"sentence": "there are 7 people"})
    # Once an input is run through the workflow as on line 30,
    # we can expect the plugin mutation to create an artifact
    # as per line 4.

"""
import json
import operator
import traceback
from pprint import pformat
from typing import Any, Dict, List, Optional

import pydash as py_  # type: ignore
import pytz
import requests
from pytz.tzinfo import BaseTzInfo  # type: ignore

from dialogy import constants as const
from dialogy.base.entity_extractor import EntityExtractor
from dialogy.base.plugin import PluginFn
from dialogy.constants import EntityKeys
from dialogy.types.entity import BaseEntity, dimension_entity_map
from dialogy.utils import dt2timestamp
from dialogy.utils.logger import dbg, log


class DucklingPlugin(EntityExtractor):
    """
    A :ref:`Plugin<plugin>` for extracting entities using `Duckling <https://github.com/facebook/duckling>`_. Once
    instantiated, a :code:`duckling_parser` object will interface to an http server, running `Duckling
    <https://github.com/facebook/duckling>`_.

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

    def __init__(
        self,
        dimensions: List[str],
        timezone: str,
        timeout: float = 0.5,
        url: str = "http://0.0.0.0:8000/parse",
        locale: str = "en_IN",
        datetime_filters: Optional[str] = None,
        threshold: Optional[float] = None,
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        entity_map: Optional[Dict[str, Any]] = None,
        debug: bool = False,
    ) -> None:
        """
        constructor
        """
        super().__init__(access=access, mutate=mutate, debug=debug, threshold=threshold)
        self.dimensions = dimensions
        self.locale = locale
        self.timezone = timezone
        self.timeout = timeout
        self.url = url
        self.reference_time: Optional[int] = None
        self.datetime_filters = datetime_filters
        self.headers: Dict[str, str] = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }

        if isinstance(entity_map, dict):
            self.dimension_entity_map = {**dimension_entity_map, **entity_map}
        else:
            self.dimension_entity_map = dimension_entity_map

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

    @dbg(log)
    def __create_req_body(
        self, text: str, reference_time: Optional[int], locale: str = "en_IN"
    ) -> Dict[str, Any]:
        """
        create request body for entity parsing

        example: "3 people tomorrow"

        Make your own reference time using the current timestamp using: :code:`int(datetime.now().timestamp() * 1000)`
        These are the seconds since the `Unix epoch <https://en.wikipedia.org/wiki/Unix_time>`_

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

        payload = {
            "text": text,
            "locale": locale or self.locale,
            "tz": self.__set_timezone(),
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
        }
        log.debug("Duckling API payload:")
        log.debug(pformat(payload))

        return payload

    @dbg(log)
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

        if filter_type in self.DATETIME_OPERATION_ALIAS:
            operation = self.DATETIME_OPERATION_ALIAS[filter_type]
        else:
            try:
                operation = getattr(operator, filter_type)
            except (AttributeError, TypeError) as exception:
                log.debug(traceback.format_exc())
                raise ValueError(
                    f"Expected datetime_filters to be one of {self.FUTURE}, {self.PAST} "
                    "or a valid comparison operator here: https://docs.python.org/3/library/operator.html"
                ) from exception

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

    @dbg(log)
    def _reshape(
        self, entities_json: List[Dict[str, Any]], alternative_index: int = 0
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
        entity_object_list: List[BaseEntity] = []

        try:
            # For each entity dict:
            for entity in entities_json:
                if entity[EntityKeys.VALUE][EntityKeys.TYPE] in [
                    EntityKeys.VALUE,
                    EntityKeys.DURATION,
                    EntityKeys.INTERVAL,
                ]:
                    # We can auto convert dict forms of duckling entities to dialogy entity classes only if they are
                    # known in advance. We currently support only the types in the condition above.
                    if entity[EntityKeys.VALUE][EntityKeys.TYPE] == EntityKeys.INTERVAL:
                        # Duckling entities with interval type have a different structure for value(s).
                        # They have a need to express units in "from", "to" format.
                        cls = self.dimension_entity_map[entity[EntityKeys.DIM]][EntityKeys.INTERVAL]  # type: ignore
                    else:
                        cls = self.dimension_entity_map[entity[EntityKeys.DIM]][EntityKeys.VALUE]  # type: ignore
                    # The most appropriate class is picked for making an object from the dict.
                    duckling_entity = cls.from_dict(entity)
                    # Depending on the type of entity, the value is searched and filled.
                    duckling_entity.set_value()
                    duckling_entity.alternative_index = alternative_index
                    # Collect the entity object in a list.
                    entity_object_list.append(duckling_entity)
                else:
                    # Raised only if an unsupported `dimension` is used.
                    raise NotImplementedError(
                        f"Entities with value.type {entity['value']['type']} are"
                        " not implemented. Report this"
                        " issue here: https://github.com/Vernacular-ai/dialogy/issues"
                    )
        except KeyError as key_error:
            # Being vary of structural changes in the API or entity dicts.
            # Under normal circumstances this error shouldn't be raised.
            log.debug(traceback.format_exc())
            raise KeyError(
                f"Missing key {key_error} in entity {entity}."
            ) from key_error
        return entity_object_list

    def _get_entities(
        self, text: str, locale: str = "en_IN", reference_time: Optional[int] = None
    ) -> List[Dict[str, Any]]:
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
        :return: Duckling entities as python :code:`dicts`.
        :rtype: List[Dict[str, Any]]
        """
        body = self.__create_req_body(text, reference_time, locale)

        try:
            response = requests.post(
                self.url, data=body, headers=self.headers, timeout=self.timeout
            )

            if response.status_code == 200:
                # The API call was successful, expect the following to contain entities.
                # A list of dicts or an empty list.
                return response.json()
        except requests.exceptions.Timeout as timeout_exception:
            log.error("Duckling timed out: %s", timeout_exception)
            log.error(pformat(body))
            return []

        # Control flow reaching here would mean the API call wasn't successful.
        # To prevent rest of the things from crashing, we will raise an exception.
        raise ValueError(
            f"Duckling API call failed | [{response.status_code}]: {response.text}"
        )

    def utility(self, *args: Any) -> List[BaseEntity]:
        """
        Produces Duckling entities, runs with a :ref:`Workflow's run<workflow_run>` method.

        :param args: Expects a tuple of :code:`Tuple[natural language for parsing entities, reference time in seconds, locale]`
        :type args: Tuple(str, int, str)
        :return: A list of duckling entities.
        :rtype: List[BaseEntity]
        """
        list_of_entities: List[List[Dict[str, Any]]] = []
        shaped_entities: List[List[BaseEntity]] = []

        input_, reference_time, locale = args
        if not isinstance(reference_time, int) and self.datetime_filters:
            raise TypeError(
                "Duckling requires reference_time to be a unix timestamp (int) but"
                f" {type(reference_time)} was found"
                "https://stackoverflow.com/questions/20822821/what-is-a-unix-timestamp-and-why-use-it\n"
            )

        self.reference_time = reference_time
        input_size = 1

        try:
            if isinstance(input_, str):
                list_of_entities.append(
                    self._get_entities(input_, locale, reference_time=reference_time)
                )
            elif isinstance(input_, list) and all(
                isinstance(text, str) for text in input_
            ):
                input_size = len(input_)
                for text in input_:
                    entities = self._get_entities(
                        text, locale, reference_time=reference_time
                    )
                    list_of_entities.append(entities)
            else:
                raise TypeError(f"Expected {input_} to be a List[str] or str.")

            for (alternative_index, entities) in enumerate(list_of_entities):
                shaped_entities.append(self._reshape(entities, alternative_index))

            shaped_entities_flattened = py_.flatten(shaped_entities)
            aggregate_entities = self.entity_consensus(
                shaped_entities_flattened, input_size
            )
            return self.apply_filters(aggregate_entities)
        except ValueError as value_error:
            raise ValueError(str(value_error)) from value_error
