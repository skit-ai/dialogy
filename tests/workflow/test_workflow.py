import pytest
from dialogy.workflow import Workflow


def test_workflow_get_input():
    workflow = Workflow(preprocessors=[], postprocessors=[])
    assert workflow.input is None, "workflow.get_input() is not None."


def test_workflow_set_output():
    workflow = Workflow(preprocessors=[], postprocessors=[])
    workflow.output = 10
    assert workflow.output == 10, "workflow.get_output() should == 10."


def test_workflow_load_model_error():
    workflow = Workflow(preprocessors=[], postprocessors=[])
    with pytest.raises(NotImplementedError):
        workflow.load_model()


def test_workflow_postprocessors_not_list_error():
    with pytest.raises(TypeError):
        workflow = Workflow(preprocessors=[], postprocessors=10)


def test_workflow_preprocessors_not_list_error():
    with pytest.raises(TypeError):
        workflow = Workflow(preprocessors=10, postprocessors=[])


def test_workflow_run():
    def mock_postproc(w):
        w.output = 10

    def mock_preproc(w):
        w.input = 20

    workflow = Workflow(preprocessors=[mock_preproc], postprocessors=[mock_postproc])

    workflow.run(2)
    assert workflow.input == 20, "workflow.get_input() should be 2."
    assert workflow.output == 10, "workflow.get_output() should be 10."


def test_workflow_run_debug_mode():
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


def test_child_class_inference_not_implemented_error():
    class Wkflw(Workflow):
        pass

    w = Wkflw(preprocessors=[], postprocessors=[])
    with pytest.raises(NotImplementedError):
        w.inference()


def test_not_callable_pre_post_processors_type_error():
    workflow = Workflow(preprocessors=[2], postprocessors=[3])

    with pytest.raises(TypeError):
        workflow.preprocess()

    with pytest.raises(TypeError):
        workflow.postprocess()
