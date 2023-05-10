from dialogy.base import Input, Output
from dialogy.plugins.text.oos_filter import OOSFilterPlugin
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", load_tests("oos_filter", __file__))
async def test_oos_filter(payload) -> None:
    intent_oos = payload["intent_oos"]

    if not isinstance(payload["threshold"], float):
        with pytest.raises(EXCEPTIONS[payload["exception"]]):
            oos_filter = OOSFilterPlugin(
                dest="output.intents",
                threshold=payload["threshold"],
                replace_output=True,
                intent_oos=intent_oos,
            )
    
    elif not isinstance(payload["intent_oos"], str):
        with pytest.raises(EXCEPTIONS[payload["exception"]]):
            oos_filter = OOSFilterPlugin(
                dest="output.intents",
                threshold=payload["threshold"],
                replace_output=True,
                intent_oos=intent_oos,
            )

    else:
        oos_filter = OOSFilterPlugin(
            dest="output.intents",
            threshold=payload["threshold"],
            replace_output=True,
            intent_oos=intent_oos,
        )

        # Create a mock workflow
        workflow = Workflow([oos_filter])
        intent_name = payload["original_intent"]
        body = [[{"transcript": payload["transcript"]}]]
        intent = Intent(name=intent_name, score=payload["predicted_confidence"])
        
        if payload["empty_intents"]:
            output = Output(intents=[])
            with pytest.raises(EXCEPTIONS[payload["exception"]]):
                _, output = await workflow.run(Input(utterances=body), output)

        else:
            output = Output(intents=[intent])
            _, output = await workflow.run(Input(utterances=body), output)

            assert output.intents[0].name == payload["expected_intent"]
