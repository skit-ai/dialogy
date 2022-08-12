import pytest

from dialogy import plugins
from dialogy.base import Input, Output
from dialogy.types import Intent
from dialogy.workflow import Workflow
from dialogy import plugins
from dialogy.types import AddressEntity
from dialogy.plugins.text.address_parser.maps import get_house_number
from tests import  load_tests


def parser_func(
    most_confident_transcription: str,
    country_code: str = "in",
    language: str = "en",
    pin: str = "",
    location: str = None,
    **kwargs,
) -> str:
    house_number_from_transcript = get_house_number(most_confident_transcription)

    return f"{house_number_from_transcript} {most_confident_transcription.replace(house_number_from_transcript, '')} {pin}"


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_address_parser_plugin(payload) -> None:

    input_ = Input(**payload["input"])
    output = Output(
        intents=[
            Intent(
                name=x["name"],
                alternative_index=x["alternative_index"],
                parsers=x["parsers"],
                slots=x["slots"],
            )
            for x in payload["output"]["intents"]
        ],
        entities=[AddressEntity.from_dict(x) for x in payload["output"]["entities"]],
    )
    expected = Output(
        intents=[
            Intent(
                name=x["name"],
                alternative_index=x["alternative_index"],
                parsers=x["parsers"],
                slots=x["slots"],
            )
            for x in payload["expected"]["intents"]
        ],
        entities=[AddressEntity.from_dict(x) for x in payload["expected"]["entities"]],
    )

    address_plugin = plugins.AddressParserPlugin(
        dest="output.entities",
        provider="google",
        address_capturing_intents="inform_address",
        country_code="IND",
        language="en",
        pincode_capturing_intents="inform_pincode",
        pincode_slot_name="pincode",
    )
    address_plugin.provider_fn = parser_func

    workflow = Workflow([address_plugin])
    workflow.input = input_
    workflow.output = output

    address_plugin(workflow)

    assert expected == workflow.output
