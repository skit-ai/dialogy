"""
Module provides types

Import Types:
    - Alternative
    - Utterance
"""
from typing import Dict, List, Optional, Union

Transcript = str
Alternative = Dict[str, Union[str, Optional[float]]]
Utterance = List[Alternative]
