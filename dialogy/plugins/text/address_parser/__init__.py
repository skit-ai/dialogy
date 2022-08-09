from typing import Any, Dict, List, Optional
import copy

from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types import AddressEntity, PincodeEntity

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
        pincode = ""
        matching_address = None

        entities = input_.find_entities_in_history(intent_name=self.pincode_capturing_intents, slot_name=self.pincode_slot_name)
        entities = [entity for entity in entities if entity["type"]=="pincode"]
         
        pincode =  PincodeEntity.from_dict(entities[0]).get_value()
        
        first_intent, *rest = intents
        
        if (not intents) or (not isinstance(intents, list)):
            return
        
        if first_intent.name in self.address_capturing_intents and pincode != "": #parallel API calls
            
            matching_address = self.provider_fn(input_.best_transcript,
                country_code=self.country_code,
                language=self.language,
                pin=pincode,
                location=self.location
            )
        if first_intent.name in self.address_capturing_intents and not matching_address:
            matching_address = self.provider_fn(input_.best_transcript,
                country_code=self.country_code,
                language=self.language,
                location=self.location
            )
            
        if matching_address:
            matching_address = AddressEntity.from_maps(input_.best_transcript, matching_address, 0)
            matching_address.add_parser(self)
        
        if matching_address:
            return [matching_address] #don't return none
        
        return []
