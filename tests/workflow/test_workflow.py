import pytest

from dialogy.workflow import Workflow


def test_workflow_get_input() -> None:
    """
    Basic initialization.
    """
    workflow = Workflow(preprocessors=[], postprocessors=[])
    assert workflow.input == {}, "workflow.get_input() is a dict()."


def test_workflow_set_output() -> None:
    """
    We can set output and input as anything.
    """
    workflow = Workflow(preprocessors=[], postprocessors=[])
    workflow.output = 10
    assert workflow.output == 10, "workflow.get_output() should == 10."


def test_workflow_load_model_error() -> None:
    """
    `load_model` has to be defined by the subclass.
    """
    workflow = Workflow(preprocessors=[], postprocessors=[])
    with pytest.raises(NotImplementedError):
        workflow.load_model()


def test_workflow_postprocessors_not_list_error() -> None:
    """
    postprocessrors should be of type [`PluginFn`](../../plugin/test_plugins.html).
    """
    with pytest.raises(TypeError):
        _ = Workflow(preprocessors=[], postprocessors=10)  # type: ignore


def test_workflow_preprocessors_not_list_error() -> None:
    """
    preprocessors should be of type [`PluginFn`](../../plugin/test_plugins.html)
    """
    with pytest.raises(TypeError):
        _ = Workflow(preprocessors=10, postprocessors=[])  # type: ignore


def test_workflow_run() -> None:
    """
    Trivial setup.
    """

    def mock_postproc(w) -> None:
        w.output = 10

    def mock_preproc(w) -> None:
        w.input = 20

    workflow = Workflow(preprocessors=[mock_preproc], postprocessors=[mock_postproc])

    # initially the value of workflow.input is = 2
    workflow.run(2)

    # once the run method is complete, the value of input and output is modified by the
    # mock_postproc and mock_preproc functions.
    assert workflow.input == 20, "workflow.get_input() should be 20."
    assert workflow.output == 10, "workflow.get_output() should be 10."


def test_child_class_inference_not_implemented_error() -> None:
    """
    Sub-classes should implement the `inference` method.
    """

    class Wkflw(Workflow):
        pass

    w = Wkflw(preprocessors=[], postprocessors=[])
    with pytest.raises(NotImplementedError):
        w.inference()


def test_not_callable_pre_post_processors_type_error() -> None:
    """"""
    workflow = Workflow(preprocessors=[2], postprocessors=[3])  # type: ignore

    with pytest.raises(TypeError):
        workflow.preprocess()

    with pytest.raises(TypeError):
        workflow.postprocess()


def test_workflow_run_debug_mode() -> None:
    """
    This test is just to get coverage.
    """

    def mock_postproc(w):
        w.output = 10

    def mock_preproc(w):
        w.input = 20

    workflow = Workflow(
        preprocessors=[mock_preproc], postprocessors=[mock_postproc], debug=True
    )

    workflow.run(2)

    assert workflow.input == 20, "workflow.get_input() should be 2."
    assert workflow.output == 10, "workflow.get_output() should be 10."


def test_workflow_flush() -> None:
    """
    Trivial setup.
    """

    def mock_postproc(w) -> None:
        w.output = 10

    def mock_preproc(w) -> None:
        w.input = 20

    workflow = Workflow(preprocessors=[mock_preproc], postprocessors=[mock_postproc])

    # initially the value of workflow.input is = 2
    workflow.run(2)

    # once the run method is complete, the value of input and output is modified by the
    # mock_postproc and mock_preproc functions.
    assert workflow.input == 20, "workflow.get_input() should be 20."
    assert workflow.output == 10, "workflow.get_output() should be 10."
    workflow.flush()
    assert workflow.input == {}, "workflow.get_input() should be dict()."
    assert workflow.output == {}, "workflow.get_output() should be dict()."


def test_workflow_json() -> None:
    """
    Test if the workflow can be made a python dictionary.
    """

    def mock_postproc(w) -> None:
        w.output = 10

    def mock_preproc(w) -> None:
        w.input = 20

    workflow = Workflow(preprocessors=[mock_preproc], postprocessors=[mock_postproc])
    workflow.run(1)
    assert workflow.json() == {"input": 20, "output": 10}
