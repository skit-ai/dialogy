from abc import ABC
from typing import Optional
from dialogy.types.plugins import PluginFn


class Plugin(ABC):
    def exec(self, access: Optional[PluginFn] = None, mutate: Optional[PluginFn] = None) -> None:
        pass
