from typing import Any, Dict, Optional

from dialogy.plugin import Plugin, PluginFn
from dialogy.types import BaseEntity
from dialogy.workflow import Workflow


class ListEntityPlugin(Plugin):
    def __init__(
        self,
        list_type: str,
        entity_map: Dict[str, BaseEntity],
        access: Optional[PluginFn],
        mutate: Optional[PluginFn],
        debug: bool = False,
    ):
        super().__init__(access=access, mutate=mutate, debug=debug)
        self.list_type = list_type
        self.entity_map = entity_map

    def utility(self, workflow: Workflow, *args: Any) -> Any:
        return []
