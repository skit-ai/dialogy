from abc import ABC
from typing import Optional
from dialogy.types.plugins import PluginFn


class Plugin(ABC):
    def __init__(self) -> None:
        super().__init__()

    def exec(self, access: Optional[PluginFn] = None, mutate: Optional[PluginFn] = None) -> None:
        pass
