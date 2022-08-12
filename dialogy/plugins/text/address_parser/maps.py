from email.policy import strict
import os
import uuid

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
mapmyindia = mapmyindia.MapMyIndia(MMI_CLIENT_ID, MMI_CLIENT_SECRET)


def get_matching_address_from_gmaps_autocomplete(
    most_confident_transcription: str, country_code: str = "in", language: str = "en", pin: str = "", location: str=None, **kwargs
) -> str:
    """Get the matching address from autocomplete results

    :param most_confident_transcription: most confident transcript
    :type most_confident_transcription: str
    :return: matching address
    :rtype: str
    """
    matching_address = ""
    strict_bounds = False

    if location:
        strict_bounds = True

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
                location=location,
                strict_bounds=strict_bounds,
            )

            if response:
                matching_address = response[0].get("description", "")
                logger.debug(f"matching_address: {matching_address}")

                if (
                    house_number_from_transcript
                    and is_house_number_absent_from_response(matching_address)
                ):
                    matching_address = (
                        f"{house_number_from_transcript} {matching_address}"
                    )

        except googlemaps.exceptions.ApiError as e:
            logger.error(e)
    return matching_address


def get_house_number(most_confident_transcription):
    house_number_from_transcript = ""
    numbers = get_all_numbers_from_a_string(most_confident_transcription)

    if (
        len(numbers) > 1
    ):  # if there are multiple numbers take the first one as house number
        house_number_from_transcript = numbers[0]

    elif len(numbers) == 1:  # if there is only one number in the transcript
        for idx, word in enumerate(most_confident_transcription.split()):
            if (
                word == numbers[0] and idx < 3
            ):  # if the number is in the first 3 words of the transcript
                house_number_from_transcript = numbers[0]
                break

    return house_number_from_transcript


def is_house_number_absent_from_response(matching_address):
    numbers = get_all_numbers_from_a_string(matching_address)
    if len(numbers) == 0:
        return True

    elif len(numbers) == 1:
        for idx, word in enumerate(matching_address.split()):
            if (
                word == numbers[0] and idx < 3
            ):  # if the number is in the first 3 words of the transcript
                return False
        return True  # a number is present in the response but it is not in the first 3 words of the response so house number must be absent
    return False


def get_all_numbers_from_a_string(string):
    numbers = []
    for word in string.split():
        if word.isdigit():
            numbers.append(word)
    return numbers


def get_address_from_mapmyindia_geocode(
    most_confident_transcription: str,
    country_code: str = "ind",
    pin: str = None,
    **kwargs
) -> str:

    matching_address = ""
    confidence = ""
    geocode_level = ""
    try:
        if most_confident_transcription:

            house_number_from_transcript = get_house_number(
                most_confident_transcription
            )
            response = mapmyindia.geocode(
                address=most_confident_transcription,
                region=country_code,
                pin=pin,
            )

            if response:

                candidates = response.get("copResults", {})
                matching_address = candidates.get("formattedAddress", "")
                confidence = candidates.get("confidenceScore", "")
                geocode_level = candidates.get("geocodeLevel", "")
                logger.debug(f"matching_address: {matching_address}")

                if (
                    house_number_from_transcript
                    and is_house_number_absent_from_response(matching_address)
                ):

                    matching_address = (
                        f"{house_number_from_transcript} {matching_address}"
                    )

    except Exception as e:
        logger.error(e)
    return matching_address
