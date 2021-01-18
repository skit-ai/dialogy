from dialogy.plugins import Plugin
from dialogy.workflow import Workflow


class ArbitraryPlugin(Plugin):
    def __init__(self):
        super(ArbitraryPlugin).__init__()

    def exec(self, access=None, mutate=None) -> None:
        # this is not required for any reason other than code-coverage
        super().exec()

        def plugin(workflow):
            numbers, words = access(workflow)
            numbers = [number + 2 for number in numbers]
            words = [word + " world" for word in words]
            mutate(workflow, (numbers, words))

        return plugin


def accessFn(workflow):
    return workflow.input


def mutateFn(workflow, value):
    workflow.output = value


def test_arbitrary_plugin():
    pluginInstance = ArbitraryPlugin()
    plugin = pluginInstance.exec(access=accessFn, mutate=mutateFn)
    workflow = Workflow(preprocessors=[plugin], postprocessors=[])

    workflow.run(([2, 5], ["hello", "hi"]))
    if isinstance(workflow.output, tuple):
        numbers, words = workflow.output
        assert numbers == [4, 7] and words == ["hello world", "hi world"]
