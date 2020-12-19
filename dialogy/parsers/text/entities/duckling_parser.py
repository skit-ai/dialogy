"""
Parser for Duckling, the open source project. 
We need this for parsing and extracting date, time, numbers, currency etc. 
We will expect Duckling to be running as an http service, and provide means
to connect from the implementation here. 
"""
import json
import datetime
from typing import List, Dict, Callable, Optional

import attr
import requests
from requests.exceptions import ConnectionError, ReadTimeout

from dialogy.plugins import Plugin
from dialogy.types.plugins import PluginFn
from dialogy.utils.logger import log


@attr.s
class DucklingParser(Plugin):
    """
    We use duckling for extracting entity tokens and parsing their value.

    Args:
        Plugin ([type]): [description]
    """
    url: str = attr.ib(default="http://0.0.0.0:8080/parse")
    dimensions: List[str] = attr.Factory(list)
    locale: str = attr.ib()
    timezone: Optional[datetime.datetime] = attr.ib()
    transformers: List[Callable] = attr.Factory(list)
    timeout: Optional[int] = attr.ib(default=None)
    headers: Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    debug: bool = attr.ib(default=False)

    def __create_req_body(self, text: str, reference_time: int):
        """[summary]

        Args:
            text (str): [description]
            reference_time (int): [description]

        Returns:
            [type]: [description]
        """
        dimensions = self.dimensions
        return {
            "text": text,
            "locale": self.locale,
            "tz": self.timezone,
            "dims": json.dumps(dimensions),
            "reftime": reference_time,
        }

    def service(self, text: str, reference_time: int):
        body = self.__create_req_body(text, reference_time)
        try:
            response = requests.post(self.url,
                                     data=body,
                                     headers=self.headers,
                                     timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            else:
                log.error("Duckling request failed [reason]: %s\n"
                          "for text=%s with reference_time=%d", response.text, text, reference_time)
                return []
        except (ConnectionError, ReadTimeout) as connection_error:
            log.error("%s : was encountered\nfor text=%s with "
                      "reference_time=%d", str(connection_error), text, reference_time)
            return []

    def exec(self, access: PluginFn, mutate: PluginFn, ref_time: int) -> None:
        pass
