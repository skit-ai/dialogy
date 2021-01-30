import attr
from typing import Optional
from dialogy.plugins import Plugin
from dialogy.workflow import Workflow
from dialogy.types.plugins import PluginFn


@attr.s
class ArbitraryPlugin(Plugin):
    access: Optional[PluginFn] = attr.ib(default=None)
    mutate: Optional[PluginFn] = attr.ib(default=None)

    def plugin(self, workflow):
        access = self.access
        mutate = self.mutate
        numbers, words = access(workflow)
        numbers = [number + 2 for number in numbers]
        words = [word + " world" for word in words]
        mutate(workflow, (numbers, words))

    def exec(self) -> PluginFn:
        # this is not required for any reason other than code-coverage
        super().exec()
        return self.plugin


def accessFn(workflow):
    return workflow.input


def mutateFn(workflow, value):
    workflow.output = value


def test_arbitrary_plugin():
    plugin_instance = ArbitraryPlugin(access=accessFn, mutate=mutateFn)
    workflow = Workflow(preprocessors=[plugin_instance.exec()], postprocessors=[])

    workflow.run(([2, 5], ["hello", "hi"]))
    if isinstance(workflow.output, tuple):
        numbers, words = workflow.output
        assert numbers == [4, 7] and words == ["hello world", "hi world"]
