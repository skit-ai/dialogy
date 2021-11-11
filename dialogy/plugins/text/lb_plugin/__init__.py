from typing import Any, Dict, List, Optional

from dialogy import constants as const
from dialogy.base.plugin import PluginFn
from dialogy.plugins import DucklingPlugin
from dialogy.types.entity import BaseEntity


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
        access: Optional[PluginFn] = None,
        mutate: Optional[PluginFn] = None,
        entity_map: Optional[Dict[str, Any]] = None,
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
            access=access,
            mutate=mutate,
            entity_map=entity_map,
            reference_time_column=reference_time_column,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
        )

    def utility(self, *args: Any) -> List[BaseEntity]:
        entity_list = super().utility(*args)
        alt_index = -1
        list_index = -1
        new_list = []
        for idx, entity in enumerate(entity_list):
            if (entity.type == "datetime" or entity.type == "date"):
                if alt_index == -1:
                    alt_index = entity.alterative_index
                    list_index = idx
                elif entity.alternative_index < alt_index:
                    alt_index = entity.alternative_index
                    list_index = idx
            else
                new_list.append(entity)
        if len(entity_list) > 0 and list_index != -1:
            new_list.append(entity_list[list_indx])
        return new_list
