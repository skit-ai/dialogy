from typing import Any, Dict, List, Optional
import copy

from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types.entity import address

from dialogy.plugins.text.address_parser.maps import (
    get_address_from_mapmyindia_geocode,
    get_matching_address_from_gmaps_autocomplete,
)


class AddressParserPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        access: Optional[Plugin] = None,
        provider: str = None,
        address_capturing_intents: List[str] = None,
        pincode_capturing_intents: List[str] = None,
        pincode_slot_name: str = None,
        country_code: str = None,
        language: str = None,
        location: str = None,
        debug: bool = False,
        **kwargs
    ) -> None:
        """A Plugin to hit the Google Maps API to fill the slot with the returned address"""
        super().__init__(dest=dest,
            debug=debug, **kwargs
        )
        self.address_capturing_intents = address_capturing_intents
        self.pincode_capturing_intents = pincode_capturing_intents
        self.pincode_slot_name = pincode_slot_name
        self.country_code = country_code
        self.language = language
        self.location = location


        provider_functions = {
                            "google": get_matching_address_from_gmaps_autocomplete, 
                            "mmi": get_address_from_mapmyindia_geocode
                            }
        self.provider_fn = provider_functions[provider]

    def utility(self, input_: Input, output: Output) -> Any:
        
        intents = output.intents
        context = input_

        pincode = ""
        matching_address = None

        # Create a function out of this
        pincode_slot = context.find_slot(intent_name=self.pincode_capturing_intents, slot_name=self.pincode_slot_name)

        if pincode_slot:
            pincode = pincode_slot["values"][0]["value"]
        
        first_intent, *rest = intents
        
        if (not intents) or (not isinstance(intents, list)):
            return
        
        if first_intent.name in self.address_capturing_intents:
            
            if pincode != "":    
                matching_address = self.provider_fn(context.best_transcript,
                    country_code=self.country_code,
                    language=self.language,
                    pin=pincode,
                    location=self.location
                )
            if not matching_address:
                matching_address = self.provider_fn(context.best_transcript,
                    country_code=self.country_code,
                    language=self.language,
                    location=self.location
                )
            
            if matching_address:
                matching_address = address.AddressEntity.from_maps(context.best_transcript, matching_address, 0)
                matching_address.add_parser(self)
        
        return [matching_address]
