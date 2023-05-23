from dialogy.base import Input, Output
from dialogy.plugins.text.oos_filter import OOSFilterPlugin
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow
from tests import EXCEPTIONS, load_tests
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", load_tests("oos_filter", __file__))
def test_oos_filter(payload) -> None:
    threshold = payload.get("threshold")
    intent_oos = payload.get("intent_oos")
    intent_threshold_map_path = payload.get("intent_threshold_map_path")
    if (
        (threshold is None and intent_threshold_map_path is None)
        or (threshold is not None and not isinstance(threshold, float))
        or (intent_oos is not None and not isinstance(intent_oos, str))
        or (
            intent_threshold_map_path is not None
            and not isinstance(intent_threshold_map_path, str)
        )
    ):
        with pytest.raises(EXCEPTIONS[payload["exception"]]):
            OOSFilterPlugin(
                dest="output.intents",
                threshold=threshold,
                replace_output=True,
                intent_oos=intent_oos,
                intent_threshold_map_path=intent_threshold_map_path,
            )
    else:
        oos_filter = OOSFilterPlugin(
            dest="output.intents",
            threshold=threshold,
            replace_output=True,
            intent_oos=intent_oos,
            intent_threshold_map_path=payload.get("intent_threshold_map_path"),
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
