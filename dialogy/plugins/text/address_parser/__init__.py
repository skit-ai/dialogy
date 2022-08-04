from typing import Any, Dict, List, Optional
import copy

from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types import Intent
from dialogy.types.slots import Slot
from dialogy.types.entity import address

from maps import (
    get_address_from_mapmyindia_geocode,
    get_matching_address_from_gmaps_autocomplete,
)


class MapsAPIPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        access: Optional[Plugin] = None,
        provider: str = None,
        address_capturing_intents: List[str] = None,
        pincode_capturing_intents: List[str] = None,
        country_code: str = None,
        language: str = None,
        debug: bool = False,
    ) -> None:
        """A Plugin to hit the Google Maps API to fill the slot with the returned address"""
        super().__init__(
            debug=debug,
        )
        self.address_capturing_intents = address_capturing_intents
        self.pincode_capturing_intents = pincode_capturing_intents
        self.country_code = country_code
        self.language = language

        provider_functions = {
                            "google": get_matching_address_from_gmaps_autocomplete, 
                            "mmi": get_address_from_mapmyindia_geocode
                            }
        self.provider_fn = provider_functions[provider]

    def utility(self, input_: Input, output: Output) -> Any:
        
        intents = output.intents
        context = input_

        pincode = None
        matching_address = None

        # Create a function out of this
        pincode_slot = context.find_slot(intent_name=self.pincode_capturing_intents, slot_name=self.pincode_slot_name)

        if pincode_slot:
            pincode = pincode_slot["values"][0]["value"]
        
        first_intent, *rest = intents
        
        if (not intents) or (not isinstance(intents, list)):
            return

        if first_intent.name in self.address_capturing_intents:
            
            if pincode:    
                matching_address = self.provider_fn(most_confident_transcript=context.best_transcript,
                    country_code=self.country_code,
                    language=self.language,
                    pin=pincode
                )
            if not matching_address:
                matching_address = self.provider_fn(most_confident_transcript=context.best_transcript,
                    country_code=self.country_code,
                    language=self.language
                )
      
            if matching_address:
                matching_address = address(context.best_transcript, matching_address, 0)

        return [matching_address]
