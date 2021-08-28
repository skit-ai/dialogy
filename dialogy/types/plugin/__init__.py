"""
Module provides access to pre-defined plugin types.

Import Types:
    - PluginFn
"""
from typing import Any, Callable

PluginFn = Callable[..., Any]
