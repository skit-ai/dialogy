"""
.. _AddressParser:
"""
from typing import Any, Callable, Dict, List, Optional

import googlemaps

from dialogy.plugins.text.address_parser import mapmyindia
from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types import AddressEntity

from dialogy.plugins.text.address_parser.maps import (
    get_gmaps_address,
    get_mapmyindia_address,
)


class MissingCredentials(Exception):
    pass


class AddressParserPlugin(Plugin):
    def __init__(
        self,
        dest: Optional[str] = None,
        access: Optional[Plugin] = None,
        provider: str = "mmi",
        gmaps_api_token: Optional[str] = None,
        mmi_client_id: Optional[str] = None,
        mmi_client_secret: Optional[str] = None,
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

        if provider == "google":
            if not gmaps_api_token:
                raise MissingCredentials(
                    "Cannot find Google Maps API credentials in env"
                )
            maps_client = googlemaps.Client(key=gmaps_api_token)

        elif provider == "mmi":
            if not (mmi_client_id and mmi_client_secret):
                raise MissingCredentials(
                    "Cannot find MapmyIndia API credentials in env"
                )
            maps_client = mapmyindia.MapMyIndia(
                client_id=mmi_client_id, client_secret=mmi_client_secret
            )

        # invalid provider exception

        provider_functions: Dict[str, Callable[..., str]] = {
            "google": get_gmaps_address(maps_client),
            "mmi": get_mapmyindia_address(maps_client),
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

        # parallel API calls
        if (
            first_intent.name in self.address_capturing_intents and pincode != ""  # type: ignore
        ):

            matching_address = self.provider_fn(
                input_.best_transcript,
                country_code=self.country_code,
                language=self.language,
                pin=pincode,
            )
        if first_intent.name in self.address_capturing_intents and not matching_address:  # type: ignore
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
