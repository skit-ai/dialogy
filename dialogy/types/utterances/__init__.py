"""
Module provides types

Import Types:
    - Alternative
    - Utterance
"""
from typing import Dict, List, Optional, Union

Alternative = Dict[str, Union[str, Optional[float]]]
Utterance = List[Alternative]
