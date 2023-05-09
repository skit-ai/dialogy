"""
    EntityConversionPlugin
"""
from dialogy.base import Input, Output, Plugin, Guard
from typing import Any, List, Optional, Dict, Union, Tuple
import pydash as py_



class EntityConversionPlugin(Plugin):
    def __init__(
        self,
        conversion_options: Dict[str, List[Dict[str, Any]]],
        guards: Optional[List[Guard]] = None,
        replace_output: bool = True,
        **kwargs: Any
    ) -> None:
        super().__init__(guards=guards, replace_output=replace_output, **kwargs)
    
        self.conversion_options = conversion_options
    
    
    
    
