from abc import ABC
from typing import Callable


class Plugin(ABC):
    def __init__(self):
        super().__init__()

    def exec(self, access: Callable = None, mutate: Callable = None):
        pass
