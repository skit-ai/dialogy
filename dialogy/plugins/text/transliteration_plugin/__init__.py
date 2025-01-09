"""
This plugin transliterates text between languages, specifically handling date/time words from English to Hindi.
It should be placed after the MergeASROutputPlugin in the pipeline.
"""
import string
from typing import Any, Dict, List, Optional
from loguru import logger

import dialogy.constants as const
from dialogy.base import Guard, Input, Output, Plugin


class TransliterationPlugin(Plugin):
    """
    Transliterates English date/time words to Hindi to improve downstream processing.

    The ASR transcripts may contain English words mixed with Hindi (code-mixing),
    particularly for date and time references. This can cause issues with plugins
    like Duckling that expect consistent language usage.

    Example:
        Input: "मैंने last week Tuesday को payment किया"
        Output: "मैंने पिछला सप्ताह मंगलवार को payment किया"

    This plugin identifies English date/time words and replaces them with Hindi translations
    while preserving other words.
    """
    # Class-level constant mapping for better performance
    DATETIME_MAPPING = {
        # Days
        "monday": "सोमवार",
        "tuesday": "मंगलवार", 
        "wednesday": "बुधवार",
        "thursday": "गुरुवार",
        "friday": "शुक्रवार",
        "saturday": "शनिवार",
        "sunday": "रविवार",
        
        # Months  
        "january": "जनवरी",
        "february": "फरवरी", 
        "march": "मार्च",
        "april": "अप्रैल",
        "may": "मई",
        "june": "जून",
        "july": "जुलाई", 
        "august": "अगस्त",
        "september": "सितंबर",
        "october": "अक्तूबर",
        "november": "नवंबर",
        "december": "दिसंबर",
        
        # Times of day
        "morning": "सुबह",
        "afternoon": "दोपहर", 
        "evening": "शाम",
        "night": "रात",
        "am": "पूर्वाह्न",
        "pm": "अपराह्न",
        
        # Relative days
        "today": "आज",
        "tomorrow": "कल",
        "yesterday": "कल",
        
        # Time units
        "hour": "घंटा",
        "minute": "मिनट",
        "second": "सेकंड",
        "week": "सप्ताह",
        "month": "महीना", 
        "year": "वर्ष",

        # Modifiers
        "next": "अगला",
        "last": "पिछला",
        "first": "पहला"
    }

    def __init__(
        self,
        input_column: str = const.ALTERNATIVES,
        output_column: Optional[str] = None,
        use_transform: bool = False,
        dest: Optional[str] = None,
        guards: Optional[List[Guard]] = None,
        debug: bool = False,
        **kwargs: Any
    ) -> None:
        super().__init__(
            dest=dest,
            guards=guards,
            input_column=input_column,
            output_column=output_column,
            use_transform=use_transform,
            debug=debug,
            **kwargs
        )
        
    def map_to_hindi(self, transcript: str) -> str:
        """
        Maps English date/time words to their Hindi equivalents.
        
        Args:
            transcript: Input text containing mixed English-Hindi words
            
        Returns:
            Text with English date/time words replaced by Hindi equivalents
        """
        # Remove punctuation and convert to lowercase for consistent matching
        words = transcript.lower().translate(str.maketrans('', '', string.punctuation)).split()
        
        # Replace words that have Hindi equivalents, keep others unchanged
        translated_words = [
            self.DATETIME_MAPPING.get(word, word)
            for word in words
        ]
        return ' '.join(translated_words)

    def modify_utterances(self, utterances: List[List[Dict[str, str]]]) -> List[List[Dict[str, str]]]:
        """
        Modifies utterances by transliterating date/time words.
        
        Args:
            utterances: List of ASR transcripts with confidence scores
            
        Returns:
            Modified utterances with transliterated text
        """
        if not utterances or not utterances[0]:
            return utterances
            
        for transcript in utterances[0]:
            if 'transcript' in transcript:
                transcript['transcript'] = self.map_to_hindi(transcript['transcript'])
                
        return utterances

    async def utility(self, input_: Input, output: Output) -> Any:
        """
        Plugin utility method that processes the input utterances.
        
        Args:
            input_: Input object containing utterances
            output: Output object for results
            
        Returns:
            Modified utterances with transliterated text
        """
        logger.debug(f"Input utterances for transliteration:\n{input_.utterances}")
        modified_utterances = self.modify_utterances(input_.utterances)
        logger.debug(f"Transliterated utterances:\n{modified_utterances}")
        return modified_utterances
