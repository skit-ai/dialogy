"""
Parser for Duckling, the open source project.

We need this for parsing and extracting date, time, numbers, currency etc. 
We will expect Duckling to be running as an http service, and provide means
to connect from the implementation here.

Import classes:
    - DucklingParser
"""
import json
import datetime
from typing import List, Dict, Callable, Optional, Any

import attr
import requests

from dialogy.plugins import Plugin


@attr.s(kw_only=True)
class DucklingParser(Plugin):
    """
    We use duckling for extracting entity tokens and parsing their value.

    Attributes:
    - transformers: A list of functions that can be used for parsing Duckling entities once obtained from the service call.
    - dimensions: [read here](https://github.com/facebook/duckling#supported-dimensions)
    - locale: The format for expressing locale requires language and country name ids.
              Examples: en_IN, en_US, en_UK.
    - timezone: Pytz Timezone. This is especially important when services are deployed across different geographies
                and consistency is expected in the responses.
    - url: The address where Duckling's entity parser can be reached.
    - timeout: To prevent cases where the Duckling server is stalled, leading to poor performance for this framework as well.
    """

    transformers: List[Callable[[Any], Any]] = attr.ib(factory=list)
    dimensions: Optional[List[str]] = attr.ib(default=None)
    locale: str = attr.ib(default=None)
    timezone: Optional[datetime.datetime] = attr.ib(default=None)
    timeout: Optional[int] = attr.ib(default=None)
    url: str = attr.ib(default="http://0.0.0.0:8000/parse")
    headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }

    def __create_req_body(
        self, text: str, reference_time: Optional[int]
    ) -> Dict[str, Any]:
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
        return {
            "text": text,
            "locale": self.locale,
            "tz": self.timezone,
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
        }

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
