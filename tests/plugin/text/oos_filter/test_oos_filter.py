from dialogy.base import Input, Output
from dialogy.plugins.text.oos_filter import OOSFilterPlugin
from dialogy.types.intent import Intent
from dialogy.workflow import Workflow


def test_oos_filter() -> None:
    intent_oos = "_oos_"

    oos_filter = OOSFilterPlugin(
        dest="output.intents",
        threshold=0.1,
        replace_output=True,
        intent_oos=intent_oos,
    )

    # Create a mock workflow
    workflow = Workflow([oos_filter])
    intent_name = "already_paid"
    body = [[{"transcript": "I have already paid"}]]
    intent = Intent(name=intent_name, score=0.8)  # Not mutate to oos
    oos_intent = Intent(name=intent_oos, score=0.08)  # mutate to oos

    output_non_oos = Output(intents=[intent])
    output_oos = Output(intents=[oos_intent])
    _, output_non_oos = workflow.run(Input(utterances=body), output_non_oos)
    _, output_oos = workflow.run(Input(utterances=body), output_oos)

    assert (
        output_non_oos.intents[0].name == intent_name
        and output_oos.intents[0].name == intent_oos
    )
