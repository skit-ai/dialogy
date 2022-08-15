from optparse import Option
from typing import Any, Callable, Dict, List, Optional
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
        dest: Optional[str] = None,
        access: Optional[Plugin] = None,
        provider: str = "mmi",
        address_capturing_intents: Optional[List[str]] = None,
        pincode_capturing_intents: Optional[List[str]] = None,
        pincode_slot_name: Optional[List[str]] = None,
        country_code: Optional[str] = None,
        language: Optional[str] = None,
        debug: bool = False,
        **kwargs: Any
    ) -> None:
        """A Plugin to hit the Google Maps API to fill the slot with the returned address"""
        super().__init__(dest=dest, debug=debug, **kwargs)
        self.address_capturing_intents = address_capturing_intents
        self.pincode_capturing_intents = pincode_capturing_intents
        self.pincode_slot_name = pincode_slot_name
        self.country_code = country_code
        self.language = language

        provider_functions: Dict[str, Callable[..., str]] = {
            "google": get_matching_address_from_gmaps_autocomplete,
            "mmi": get_address_from_mapmyindia_geocode,
        }
        self.provider_fn = provider_functions[provider]

    def utility(self, input_: Input, output: Output) -> List[Optional[AddressEntity]]:

        intents = output.intents
        pincode = ""
        matching_address: Optional[str] = None
        address: Optional[AddressEntity] = None

        if (not intents) or (not isinstance(intents, list)):
            return []

        entities = input_.find_entities_in_history(
            intent_names=self.pincode_capturing_intents,
            slot_names=self.pincode_slot_name,
        )

        if entities:
            entities = [entity for entity in entities if entity["type"] == "pincode"]

            pincode = entities[0]["value"]

        first_intent, *rest = intents

        if (
            first_intent.name in self.address_capturing_intents and pincode != ""
        ):  # parallel API calls

            matching_address = self.provider_fn(
                input_.best_transcript,
                country_code=self.country_code,
                language=self.language,
                pin=pincode,
            )
        if first_intent.name in self.address_capturing_intents and not matching_address:
            matching_address = self.provider_fn(
                input_.best_transcript,
                country_code=self.country_code,
                language=self.language,
            )

        if matching_address:
            address = AddressEntity.from_maps(
                input_.best_transcript, matching_address, 0
            )
            address.add_parser(self)

        if address:
            return [address]  # don't return none

        return []
