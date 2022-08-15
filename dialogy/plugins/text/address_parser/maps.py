import os
import re
import uuid
from typing import Type, List, Dict, Any, Optional, Union

import googlemaps

from dotenv import load_dotenv

from loguru import logger
from dialogy.plugins.text.address_parser import mapmyindia

load_dotenv(override=True)
GOOGLE_MAPS_API_TOKEN = os.getenv("GOOGLE_MAPS_API_TOKEN")
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_TOKEN)
session_token = uuid.uuid4()

MMI_CLIENT_ID = os.getenv("MMI_CLIENT_ID")
MMI_CLIENT_SECRET = os.getenv("MMI_CLIENT_SECRET")
mmi: mapmyindia.MapMyIndia
mmi = mapmyindia.MapMyIndia(MMI_CLIENT_ID, MMI_CLIENT_SECRET)


def get_matching_address_from_gmaps_autocomplete(
    most_confident_transcription: str,
    country_code: str = "in",
    language: str = "en",
    pin: str = "",
    **kwargs: Any,
) -> str:
    """Get the matching address from autocomplete results

    :param most_confident_transcription: most confident transcript
    :type most_confident_transcription: str
    :return: matching address
    :rtype: str
    """
    matching_address = ""

    if most_confident_transcription:
        try:

            house_number_from_transcript = get_house_number(
                most_confident_transcription
            )

            response = gmaps.places_autocomplete(
                input_text=f"{most_confident_transcription} {pin}",
                session_token=session_token,
                components={"country": [country_code]},
                language=language,
            )
            if response:
                matching_address = response[0].get("description", "")
                logger.debug(f"matching_address: {matching_address}")

                if (
                    house_number_from_transcript
                    and is_house_number_absent_from_response(
                        house_number_from_transcript, matching_address
                    )
                ):
                    matching_address = (
                        f"{house_number_from_transcript} {matching_address}"
                    )

        except (googlemaps.exceptions.ApiError, googlemaps.exceptions.HTTPError) as e:
            logger.error(e)
    return matching_address


def get_house_number(most_confident_transcription: str) -> str:
    house_number_from_transcript: str = ""
    numbers = get_all_numbers_from_a_string(most_confident_transcription)

    if numbers:  # if there is only one number in the transcript
        for idx, word in enumerate(most_confident_transcription.split()):
            if (
                word == numbers[0] and idx < 3
            ):  # if the number is in the first 3 words of the transcript
                house_number_from_transcript = numbers[0]
                break

    return house_number_from_transcript


def is_house_number_absent_from_response(
    house_number: str, matching_address: str
) -> Any:
    numbers = get_all_numbers_from_a_string(matching_address)
    if not numbers:
        return True

    if numbers:
        for idx, word in enumerate(matching_address.replace(",", "").split()):
            if (
                word == numbers[0] and idx < 3 and word == house_number
            ):  # if the number is in the first 3 words of the transcript
                return False
        return True  # a number is present in the response but it is not in the first 3 words of the response so house number must be absent


def get_all_numbers_from_a_string(string: str) -> List[str]:
    return re.findall("\d+", string)


def get_address_from_mapmyindia_geocode(
    most_confident_transcription: str,
    country_code: str = "ind",
    pin: Optional[str] = None,
    **kwargs: Any,
) -> str:

    matching_address = ""
    confidence = ""
    geocode_level = ""
    try:
        if most_confident_transcription:

            house_number_from_transcript = get_house_number(
                most_confident_transcription
            )
            response: Optional[Dict[str, Any]] = mmi.geocode(
                address=most_confident_transcription,
                region=country_code,
                pin=pin,
            )

            if response:

                candidates: Dict[str, Any] = response.get("copResults", {})
                matching_address = candidates.get("formattedAddress", "")
                confidence = candidates.get("confidenceScore", "")
                geocode_level = candidates.get("geocodeLevel", "")
                logger.debug(f"matching_address: {matching_address}")

                if (
                    house_number_from_transcript
                    and is_house_number_absent_from_response(
                        house_number_from_transcript, matching_address
                    )
                ):

                    matching_address = (
                        f"{house_number_from_transcript} {matching_address}"
                    )

    except Exception as e:
        logger.error(e)
    return matching_address
