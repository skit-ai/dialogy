"""
Parser for Duckling, the open source project.

We need this for parsing and extracting date, time, numbers, currency etc. 
We will expect Duckling to be running as an http service, and provide means
to connect from the implementation here.

Import classes:
    - DucklingParser
"""
import json
from typing import List, Dict, Optional, Any

import attr
import requests
import pytz

from dialogy.plugins import Plugin, PluginFn
from dialogy.workflow import Workflow
from dialogy.types.entities import (
    BaseEntity,
    dimension_entity_map,
)


@attr.s(kw_only=True)
class DucklingParser(Plugin):
    """
    We use duckling for extracting entity tokens and parsing their value.

    Attributes:
    - dimensions (Optional[List[str]]): [read here](https://github.com/facebook/duckling#supported-dimensions)
    - locale (str): The format for expressing locale requires language and country name ids.
              Examples: en_IN, en_US, en_UK.
    - timezone (Optional[str]): Pytz Timezone. This is especially important when services are deployed across different geographies
                and consistency is expected in the responses.
    - timeout (Optional[int]): To prevent cases where the Duckling server is stalled, leading to poor performance for this framework as well.
    - url (str): The address where Duckling's entity parser can be reached.
    """

    dimensions: Optional[List[str]] = attr.ib(default=None)
    locale: str = attr.ib(default=None)
    timezone: Optional[str] = attr.ib(default=None)
    timeout: Optional[int] = attr.ib(default=None)
    url: str = attr.ib(default="http://0.0.0.0:8000/parse")
    headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    def __create_req_body(
        self, text: str, reference_time: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Create request body for entity parsing.

        Isolation of the request object expected by Duckling.

        Args:
            text (str): A sentence or document.
            reference_time (int): Cases where relative units of time are mentioned,
                                  like "today", "now", etc. We need to know the current time
                                  to parse the values into usable dates/times.
        """
        dimensions = self.dimensions
        payload = {
            "text": text,
            "locale": self.locale,
            "tz": None,
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
        }

        if isinstance(self.timezone, str):
            try:
                payload["tz"] = pytz.timezone(self.timezone)  # type: ignore
                return payload
            except pytz.UnknownTimeZoneError as unknown_timezone_error:
                raise pytz.UnknownTimeZoneError(
                    f"The timezone {self.timezone} is invalid"
                    " check valid types here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
                ) from unknown_timezone_error
        return payload

    def mutate_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        entity["range"] = {"start": entity["start"], "end": entity["end"]}
        entity["type"] = entity["dim"]

        if "values" in entity["value"]:
            del entity["value"]["values"]
            entity["values"] = [entity["value"]]
        else:
            entity["values"] = [entity["value"]]

        if "grain" in entity["value"]:
            entity["grain"] = entity["value"]["grain"]
        elif entity["value"]["type"] == "interval":
            entity["grain"] = entity["value"]["to"]["grain"]

        del entity["start"]
        del entity["end"]
        del entity["value"]
        return entity

    def reshape(
        self, entities_json: List[Dict[str, Any]]
    ) -> Optional[List[BaseEntity]]:
        entity_object_list: List[BaseEntity] = []

        try:
            for entity in entities_json:
                if entity["value"]["type"] == "interval":
                    cls = dimension_entity_map[entity["dim"]]["interval"]  # type: ignore
                    entity_object_list.append(cls.from_dict(self.mutate_entity(entity)))
                elif entity["value"]["type"] == "value":
                    cls = dimension_entity_map[entity["dim"]]["value"]  # type: ignore
                    entity_object_list.append(cls.from_dict(self.mutate_entity(entity)))
                else:
                    raise NotImplementedError(
                        f"Entities with value.type {entity['value']['type']} are"
                        " not implemented. Report this"
                        " issue here: https://github.com/Vernacular-ai/dialogy/issues"
                    )
        except KeyError as key_error:
            raise KeyError(
                f"Missing key {key_error} in entity {entity}."
            ) from key_error
        return entity_object_list

    def get_entities(
        self, text: str, reference_time: Optional[int]
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get entities from duckling-server.

        Assuming duckling-server is running at expected `url`. The entities are returned in
        `json` compatible format.

        Args:
            text (str): The sentence or document in which entities must be looked up.
            reference_time (int): Cases where relative units of time are mentioned,
                                  like "today", "now", etc. We need to know the current time
                                  to parse the values into usable dates/times.

        Raises:
            requests.exceptions.ConnectionError: Duckling cannot be reached at `self.url`
            requests.exceptions.Timeout: Duckling request times out.
            ValueError: The status code of the response is not 200.

        Returns:
            Optional[List[Dict[str, Any]]]: [description]
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

    def exec(
        self, access: Optional[PluginFn] = None, mutate: Optional[PluginFn] = None
    ) -> PluginFn:
        """
        [summary]

        Args:
            access (PluginFn): [description]
            mutate (PluginFn): [description]
        """

        def parse(workflow: Workflow) -> None:
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

        return parse
