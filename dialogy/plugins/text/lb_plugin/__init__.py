from typing import Any, Dict, List, Optional

from pydash import partition

from dialogy import constants as const
from dialogy.base import Guard, Input, Output
from dialogy.plugins import DucklingPlugin
from dialogy.types import BaseEntity


class DucklingPluginLB(DucklingPlugin):
    # Constructor
    def __init__(
        self,
        dimensions: List[str],
        timezone: str,
        timeout: float = 0.5,
        url: str = "http://0.0.0.0:8000/parse",
        locale: str = "en_IN",
        datetime_filters: Optional[str] = None,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        reference_time_column: str = const.REFERENCE_TIME,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        debug: bool = False,
    ):
        super().__init__(
            dimensions,
            timezone,
            timeout=timeout,
            url=url,
            locale=locale,
            datetime_filters=datetime_filters,
            threshold=0,
            dest=dest,
            guards=guards,
            reference_time_column=reference_time_column,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )

    def utility(self, input_: Input, output: Output) -> List[BaseEntity]:
        entity_list = super().utility(input_, output)
        datetime_list, other_list = partition(
            entity_list, lambda x: x.entity_type in ["datetime", "date", "time"]
        )
        if datetime_list:
            other_list.append(min(datetime_list, key=lambda x: x.alternative_index))

        return other_list
