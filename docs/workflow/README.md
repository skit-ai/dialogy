# Workflow

[[source](../../dialogy/workflow/__init__.py)]

A `workflow` is supposed to run tasks that can be anticipated well in advance. We are prioritizing tasks that can be performed in production
so you may find it odd to miss `train` and `test` methods. This is a deliberate decision since that choice is upto the user and a `workflow` 
targets performance in a production environment, where `train` and `test` are not the expected set of tasks, rather `inference` is.

A workflow accepts `preprocessors` and `postprocessors` of type [`Optional[List[PluginFn]]`](../../dialogy/types/plugins/__init__.py). Preprocessing data has clear utility in ML-pipelines. Post-processing however, tends to be useful at certain specific times. Given that `postprocessors` tend to allow bad-practices, it is highly encouraged to get most of the work done through the use of machine-learning techniques. There are still some uses (not restricted to) for a post-processing layer:

1. Eliminate low-confidence output.
2. Slot-filling.
3. Sorting items by order of confidence.

_What's slot filling?_

> The goal of Slot Filling is to identify from a running dialog, different slots, which correspond to different parameters of the user’s query. For instance, when a user queries for nearby restaurants, key slots for location and preferred food are required for a dialog system to retrieve the appropriate information. Thus, the main challenge in the slot-filling task is to extract the target entity.


## Examples

Here is an example from the tests.
```python
from dialogy.workflow import Workflow


def test_workflow_run():
    def mock_postproc(w):
        w.output = 10

    def mock_preproc(w):
        w.input = 20

    workflow = Workflow(
        preprocessors=[mock_preproc],
        postprocessors=[mock_postproc]
    )

    workflow.run(2)
    assert workflow.input == 20, "workflow.get_input() should be 20." # ✅
    assert workflow.output == 10, "workflow.get_output() should be 10." # ✅
```
refer to the [[source](../../dialogy/workflow/__init__.py)] for the `.run` method for understanding the process here.
```python
    # from the source
    def run(self, input_: Any) -> Any:
        """
        Get final results from the workflow.

        The current workflow exhibits the following simple procedure:
        pre-processing -> inference -> post-processing.

        Args:
            input_ (Any): This function receives any arbitrary input. Subclasses may enforce
            a stronger check.

        Returns:
            (Any): This function can return any arbitrary value. Subclasses may enforce a stronger check.
        """
        self.input = input_
        self.preprocess()
        self.inference()
        self.postprocess()
        return self.output
```

The utility of a `Workflow` is to inspire subclasses which can then be added to this framework for faster development. Along with the [Plugin](../plugins/README.md) ecosystem, where any plugin can attach to any subclass of `Workflow` ensures development speeds would increase over time.

## Contrib
Contributing a workflow requires a sub-class of `Workflow` with passing tests. There is no restriction on methods and their operations. 
So say a workflow `TrainableWorkflow` exists which allows users to have access to `train`, `test`, `save` methods as well, would be accepted 
into the core libraries.

There might be restriction based on uniqueness of workflows.
