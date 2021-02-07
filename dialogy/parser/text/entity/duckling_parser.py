"""
Parser for [Duckling](https://github.com/facebook/duckling), the open source project.

We use [Duckling](https://github.com/facebook/duckling) for parsing and extracting date, time, numbers, currency etc.
We will expect Duckling to be running as an http service, and provide means to connect from the implementation here.

## Tutorials

- [DucklingParser](../../../../tests/parser/text/entity/test_duckling_parser.html)

Import classes:

- DucklingParser
"""
import json
from typing import List, Dict, Optional, Any

import attr
import requests
import pytz
from pytz.tzinfo import BaseTzInfo  # type: ignore
from dialogy.constants import EntityKeys

from dialogy.plugin import Plugin, PluginFn
from dialogy.workflow import Workflow
from dialogy.types.entity import (
    BaseEntity,
    dimension_entity_map,
)


# == DucklingParser ==
@attr.s(kw_only=True)
class DucklingParser(Plugin):
    """
    [Plugin](../../../plugin/plugin.html) for extracting entities using [Duckling](https://github.com/facebook/duckling).
    Once instantiated, a `duckling_parser` object will interface to an http server, running [Duckling](https://github.com/facebook/duckling).

    This object when used as a plugin, transforms the `List[Dict[str, Any]]` returned from the API to a [BaseEntity](../../../types/entity/base_entity.html).

    Plugin signature:

    - `access(Workflow) -> (str, int)`
        - int here should be `datetime.timestamp()`.
    - `mutate(Workflow, List[BaseEntity]) -> None`
        - insert `List[BaseEntity]` into `Workflow`.

    Attributes:

    - dimensions (Optional[List[str]])
    - locale (str):
    - timezone (Optional[str]):
    - timeout (Optional[float]): (default `0.05`)
    - url (str): (default: `"http://0.0.0.0:8000/parse"`)
    """

    # **dimensions**
    #
    # [[Read](https://github.com/facebook/duckling#supported-dimensions)]
    # We support:
    # - `Numeral`
    # - `Time`
    # - `People` - This isn't part of the standard, we have a private fork to support this.
    # Do note, passing more dimensions is not free. Duckling would search for extra set of patterns just because
    # those dimensions were expected.
    dimensions: Optional[List[str]] = attr.ib(default=None)

    # **locale**
    #
    # The format for expressing locale requires language code and country name ids. [[Read](https://github.com/facebook/duckling#extending-duckling)]
    # about sections that define [ISO-639-codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) for languages and
    # [ISO3166 alpha2 country code](https://www.iso.org/obp/ui/#search/code/) for country codes.
    # Examples: `"en_IN"`, `"en_US"`, `"en_GB"`.
    locale: str = attr.ib(default=None)

    # **timezone**
    #
    # `pytz` Timezone. This is especially important when services are deployed across different geographies
    # and consistency is expected in the responses. Get a valid value from a [list of tz database timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
    # Example: `"Asia/Kolkata"`
    timezone: Optional[str] = attr.ib(default=None)

    # **timeout**
    #
    # There are certain strings which tend to stall Duckling: [example](https://github.com/facebook/duckling/issues/338).
    # In such cases, to prevent the overall experience to slow down as well, provide a certain timeout value.
    timeout: Optional[float] = attr.ib(default=0.05)

    # **url**: The address where Duckling's entity parser can be reached.
    url: str = attr.ib(default="http://0.0.0.0:8000/parse")

    headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    # == __set_timezone ==
    def __set_timezone(self) -> Optional[BaseTzInfo]:
        """
        Set timezone as BaseTzInfo from compatible timezone string.

        Raises:
            pytz.UnknownTimeZoneError: If `self.timezone` is not in [list of tz database timezones](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).

        Returns:
            [BaseTzInfo]
        """

        # If timezone is an unsafe string, we will handle a `pytz.UnknownTimeZoneError` exception
        # and pass a friendly message.
        if isinstance(self.timezone, str):
            try:
                return pytz.timezone(self.timezone)
            except pytz.UnknownTimeZoneError as unknown_timezone_error:
                raise pytz.UnknownTimeZoneError(
                    f"The timezone {self.timezone} is invalid"
                    " check valid types here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
                ) from unknown_timezone_error
        return None

    # == __create_req_body ==
    def __create_req_body(
        self, text: str, reference_time: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        create request body for entity parsing

        Args:

        - text (str): A sentence or document.
        - reference_time (Optional[int]):
        """
        dimensions = self.dimensions

        # **Payload Description**
        #
        # text - example: "3 people tomorrow"
        #
        # reftime - Resolve relative time like "yesterday", "next month", etc.
        # Make your own reference time using the current timestamp using: `int(datetime.now().timestamp() * 1000)`
        # These are the seconds since the [Unix epoch](https://en.wikipedia.org/wiki/Unix_time)
        payload = {
            "text": text,
            "locale": self.locale,
            "tz": self.__set_timezone(),
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
        }

        return payload

    # == mutate_entity ==
    @staticmethod
    def mutate_entity(entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mutate entity obtained from Duckling API.

        The purpose is to simplify BaseEntity initialization by calling `BaseEntity.from_dict(**entity)`.

        Args:
            entity (Dict[str, Any]): An entity returned from Duckling's API.

        Returns:
            Dict[str, Any]: Updated keys and structure.
        """

        # **range** describes the span of string from which the entity was found.
        entity[EntityKeys.RANGE] = {
            EntityKeys.START: entity[EntityKeys.START],
            EntityKeys.END: entity[EntityKeys.END],
        }

        # **type** of an entity is same as its **dimension**.
        entity[EntityKeys.TYPE] = entity[EntityKeys.DIM]

        # This piece is a preparation for multiple entity values.
        # So, even though we are confident of the value found, we are still keeping the
        # structure.
        if EntityKeys.VALUES in entity[EntityKeys.VALUE]:
            del entity[EntityKeys.VALUE][EntityKeys.VALUES]
        entity[EntityKeys.VALUES] = [entity[EntityKeys.VALUE]]

        # Pulling out the value of entity's **grain**. The value of **grain** helps
        # us understand the precision of the entity. Usually present for `Time` dimension
        # expect "year", "month", "day", etc.
        if EntityKeys.GRAIN in entity[EntityKeys.VALUE]:
            entity[EntityKeys.GRAIN] = entity[EntityKeys.VALUE][EntityKeys.GRAIN]
        elif entity[EntityKeys.VALUE][EntityKeys.TYPE] == EntityKeys.INTERVAL:
            entity[EntityKeys.GRAIN] = entity[EntityKeys.VALUE][EntityKeys.TO][
                EntityKeys.GRAIN
            ]

        del entity[EntityKeys.START]
        del entity[EntityKeys.END]
        del entity[EntityKeys.VALUE]
        return entity

    # == reshape ==
    def reshape(
        self, entities_json: List[Dict[str, Any]]
    ) -> Optional[List[BaseEntity]]:
        """
        Create `BaseEntity` from a list of entity dicts.

        Args:
            entities_json (List[Dict[str, Any]]): List of entities derived from Duckling's API.

        Raises:
            NotImplementedError: Raised when dimensions not supported by the project are used.
            KeyError: Expected keys in entity dict don't match the Entity class.

        Returns:
            Optional[List[BaseEntity]]: A list of Entity objects.
        """
        entity_object_list: List[BaseEntity] = []

        try:
            # For each entity dict:
            #
            # 1. Get the Entity class
            # 2. create an Entity object from the entity dict.
            for entity in entities_json:
                if entity[EntityKeys.VALUE][EntityKeys.TYPE] == EntityKeys.INTERVAL:
                    cls = dimension_entity_map[entity[EntityKeys.DIM]][EntityKeys.INTERVAL]  # type: ignore
                    entity_object_list.append(cls.from_dict(self.mutate_entity(entity)))
                elif entity[EntityKeys.VALUE][EntityKeys.TYPE] == EntityKeys.VALUE:
                    cls = dimension_entity_map[entity[EntityKeys.DIM]][EntityKeys.VALUE]  # type: ignore
                    entity_object_list.append(cls.from_dict(self.mutate_entity(entity)))
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
            raise KeyError(
                f"Missing key {key_error} in entity {entity}."
            ) from key_error
        return entity_object_list

    # == get_entities ==
    def get_entities(
        self, text: str, reference_time: Optional[int]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get entities from duckling-server.

        Assuming duckling-server is running at expected `url`. The entities are returned in
        `json` compatible format.

        Args:

        - text (str): The sentence or document in which entities must be looked up.
        - reference_time (int): Cases where relative units of time are mentioned,
                                like "today", "now", etc. We need to know the current time
                                to parse the values into usable dates/times.

        Raises:
            requests.exceptions.ConnectionError: Duckling cannot be reached at `self.url`
            requests.exceptions.Timeout: Duckling request times out.
            ValueError: The status code of the response is not 200.

        Returns:
            Optional[List[Dict[str, Any]]]
        """
        body = self.__create_req_body(text, reference_time)
        response = requests.post(
            self.url, data=body, headers=self.headers, timeout=self.timeout
        )

        if response.status_code == 200:
            # The API call was successful, expect the following to contain entities.
            # A list of dicts or an empty list.
            return response.json()

        # Control flow reaching here would mean the API call wasn't successful.
        # To prevent rest of the things from crashing, we will raise an exception.
        raise ValueError(
            f"Duckling API call failed | [{response.status_code}]: {response.text}"
        )

    # == plugin ==
    def plugin(self, workflow: Workflow) -> None:
        """
        Insert Entity objects into the workflow.

        Args:

        - workflow (Workflow)

        Raises:
            TypeError: If access and mutate functions are not callable.
        """
        access = self.access
        mutate = self.mutate
        if access and mutate:
            try:
                text, reference_time = access(workflow)
                entities_json = self.get_entities(text, reference_time)
                if entities_json:
                    entities = self.reshape(entities_json)
                    mutate(workflow, entities)
            except TypeError as type_error:
                raise TypeError(
                    "Expected `access` and `mutate` to be Callable,"
                    f" got access={type(access)} mutate={type(mutate)} | {type_error}"
                ) from type_error

        else:
            raise TypeError(
                "Expected `access` and `mutate` to be Callable,"
                f" got access={type(access)} mutate={type(mutate)}"
            )

    # == __call__ ==
    def __call__(self) -> PluginFn:
        """
        [callable-plugin](../../../plugin/plugin.html#__call__)
        """
        return self.plugin
