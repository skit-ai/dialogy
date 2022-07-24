from typing import Any, Dict, List, Optional
import copy

from dialogy.base.plugin import Plugin, Input, Output
from dialogy.types import Intent
from dialogy.types.slots import Slot

from maps import (
    get_address_from_mapmyindia_geocode,
    get_matching_address_from_gmaps_autocomplete,
)


class GoogleMapsAPIPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        access: Optional[Plugin] = None,
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

    def utility(self, input_: Input, output: Output) -> Any:
        intents: List[Intent]
        ner_input: List[str]

        intents = output.intents
        context = input_

        pincode = None

        if context.history:
            for intent in context.history[0]["intents"]:
                if intent["name"] in self.pincode_capturing_intents:
                    for slot in intent["slots"]:
                        if slot["name"] == "pincode":
                            pincode = str(slot["values"][0]["value"]).replace(" ", "")

        first_intent, *rest = intents
        slots: List[Dict[str, Any]] = first_intent.slots

        if (not intents) or (not isinstance(intents, list)):
            return

        if not slots:
            return

        if first_intent.name in self.address_capturing_intents:
            ner_input = [
                value.value
                for slot in slots
                for value in slots[slot].values
                if slot == "address"
            ]
            if not ner_input:
                return

            most_confident_transcription = ner_input[0]
            matching_address = get_matching_address_from_gmaps_autocomplete(
                most_confident_transcription,
                country_code=self.country_code,
                language=self.language,
            )

            if matching_address:
                first_intent.slots["google_maps_address"] = copy.deepcopy(
                    first_intent.slots["address"]
                )

                first_intent.slots["google_maps_address"].name = "google_maps_address"
                for slot_value in first_intent.slots["google_maps_address"].values:
                    slot_value.value = matching_address
            else:
                first_intent.slots["google_maps_address"] = Slot(
                    name="google_maps_address", values=[]
                )

            if pincode:
                matching_address = get_matching_address_from_gmaps_autocomplete(
                    " ".join(
                        [most_confident_transcription.replace(pincode, ""), pincode]
                    )
                )

                if matching_address:
                    first_intent.slots["google_maps_address-pincode"] = copy.deepcopy(
                        first_intent.slots["address"]
                    )

                    first_intent.slots[
                        "google_maps_address-pincode"
                    ].name = "google_maps_address-pincode"
                    for slot_value in first_intent.slots[
                        "google_maps_address-pincode"
                    ].values:
                        slot_value.value = matching_address
                else:
                    first_intent.slots["google_maps_address-pincode"] = Slot(
                        name="google_maps_address-pincode", values=[]
                    )

            first_intent.add_parser(self.__class__.__name__)

        return [first_intent, *rest]


class MapMyIndiaAPIPlugin(Plugin):
    def __init__(
        self,
        dest=None,
        access: Optional[Plugin] = None,
        address_capturing_intents: List[str] = None,
        pincode_capturing_intents: List[str] = None,
        debug: bool = False,
    ) -> None:
        """A Plugin to hit the MapMyIndia API to fill the slot with the returned address"""
        super().__init__(
            debug=debug,
        )
        self.address_capturing_intents = address_capturing_intents
        self.pincode_capturing_intents = pincode_capturing_intents

    def utility(self, input_: Input, output: Output) -> Any:
        intents: List[Intent]
        ner_input: List[str]

        intents = output.intents
        context = input_

        pincode = None

        if (not intents) or (not isinstance(intents, list)):
            return

        if context.history:
            for intent in context.history[0]["intents"]:
                if intent["name"] in self.pincode_capturing_intents:
                    for slot in intent["slots"]:
                        if slot["name"] == "pincode":
                            pincode = str(slot["values"][0]["value"]).replace(" ", "")

        first_intent, *rest = intents
        slots: List[Dict[str, Any]] = first_intent.slots

        if not slots:
            return

        if first_intent.name in self.address_capturing_intents:
            ner_input = [
                value.value
                for slot in slots
                for value in slots[slot].values
                if slot == "address"
            ]
            if not ner_input:
                return

            most_confident_transcription = ner_input[0]

            matching_address, _, _ = get_address_from_mapmyindia_geocode(
                most_confident_transcription
            )

            if matching_address:
                first_intent.slots["mmi_maps_address"] = copy.deepcopy(
                    first_intent.slots["address"]
                )

                first_intent.slots["mmi_maps_address"].name = "mmi_maps_address"
                for slot_value in first_intent.slots["mmi_maps_address"].values:
                    slot_value.value = matching_address

            else:
                first_intent.slots["mmi_maps_address"] = Slot(
                    name="mmi_maps_address", values=[]
                )

            if pincode:
                matching_address, _, _ = get_address_from_mapmyindia_geocode(
                    most_confident_transcription.replace(pincode, ""), pin=pincode
                )

                if matching_address:
                    first_intent.slots["mmi_maps_address-pincode"] = copy.deepcopy(
                        first_intent.slots["address"]
                    )

                    first_intent.slots[
                        "mmi_maps_address-pincode"
                    ].name = "mmi_maps_address-pincode"
                    for slot_value in first_intent.slots[
                        "mmi_maps_address-pincode"
                    ].values:
                        slot_value.value = matching_address

                else:
                    first_intent.slots["mmi_maps_address-pincode"] = Slot(
                        name="mmi_maps_address-pincode", values=[]
                    )

            first_intent.add_parser(self.__class__.__name__)
