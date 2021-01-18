"""Module provides types 

Import Types:
    - Alternative
    - Utterance
"""
from typing import List, Dict, Callable, Union, Optional


Alternative = Dict[str, Union[str, Optional[float]]]
Utterance = List[Alternative]
