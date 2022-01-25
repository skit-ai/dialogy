import json
import os
import pickle
import tempfile
from typing import List, Optional

import numpy as np
import pandas as pd
import pytest

import dialogy.constants as const
from dialogy.plugins import MergeASROutputPlugin, XLMRMultiClass
from dialogy.utils import load_file
from dialogy.workflow import Workflow
from tests import load_tests


class MockClassifier:
    def __init__(
        self,
        model_name,
        model_dir,
        num_labels: Optional[int] = None,
        args=None,
        **kwargs
    ):
        self.model_name = model_name
        self.model_dir = model_dir
        self.num_labels = num_labels
        self.args = args or {}
        self.kwargs = kwargs
        if os.path.isdir(self.model_dir):
            raise OSError("Model directory")

    def predict(self, texts: List[str]):
        if texts[0] == "<s> yes </s>":
            return [1], np.array([[-7.4609375, 7.640625]])
        elif texts[0] == "<s> no </s>":
            return [0], np.array([[7.40625, -7.5546875]])
        elif texts[0] == "<s> yes </s> <s> s </s>":
            return [1], np.array([[-7.47265625, 7.69140625]])
        elif texts[0] == "<s> 9 </s> <s> new </s> <s> no </s>":
            return [0], np.array([[7.41796875, -7.56640625]])
        else:
            return [], np.array([[]])

    def train_model(self, training_data: pd.DataFrame):
        return


def write_intent_to_workflow(w, v):
    w.output[const.INTENTS] = v


def update_input(w, v):
    w.input[const.CLASSIFICATION_INPUT] = v


def test_xlmr_plugin_no_module_error():
    save_val = const.XLMR_MODULE
    const.XLMR_MODULE = "this-module-doesn't-exist"

    with pytest.raises(ModuleNotFoundError):
        XLMRMultiClass(
            model_dir=".",
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
        )
    const.XLMR_MODULE = save_val


def test_xlmr_plugin_when_no_labelencoder_saved():
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"

    xlmr_clf = XLMRMultiClass(
        model_dir=".",
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    assert isinstance(xlmr_clf, XLMRMultiClass)
    assert xlmr_clf.model is None
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


def test_xlmr_plugin_when_labelencoder_EOFError(capsys):
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"
    _, file_path = tempfile.mkstemp(suffix=".pkl")
    save_label_encoder_file = const.LABELENCODER_FILE
    directory, file_name = os.path.split(file_path)
    const.LABELENCODER_FILE = file_name
    with capsys.disabled():
        xlmr_plugin = XLMRMultiClass(
            model_dir=directory,
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
            debug=False,
        )
        assert xlmr_plugin.model is None
    os.remove(file_path)
    const.LABELENCODER_FILE = save_label_encoder_file
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


def test_xlmr_init_mock():
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"

    xlmr_clf = XLMRMultiClass(
        model_dir=".",
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    xlmr_clf.init_model(5)
    assert xlmr_clf.model is not None

    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


def test_xlmr_init_mock():
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"

    with pytest.raises(ValueError):
        XLMRMultiClass(
            model_dir=".",
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
            args_map={"invalid": "value"},
        )
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


def test_train_xlmr_mock():
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"
    directory = "/tmp"
    file_path = os.path.join(directory, const.LABELENCODER_FILE)

    xlmr_clf = XLMRMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )

    train_df = pd.DataFrame(
        [
            {"data": "yes", "labels": "_confirm_"},
            {"data": "yea", "labels": "_confirm_"},
            {"data": "no", "labels": "_cancel_"},
            {"data": "nope", "labels": "_cancel_"},
        ]
    )

    xlmr_clf.train(train_df)

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the labelencoder saved.
    xlmr_clf_copy = XLMRMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )

    assert len(xlmr_clf_copy.labelencoder.classes_) == 2

    os.remove(file_path)
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


def test_invalid_operations():
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"

    directory = "/tmp"
    file_path = os.path.join(directory, const.LABELENCODER_FILE)
    if os.path.exists(file_path):
        os.remove(file_path)

    xlmr_clf = XLMRMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )

    with pytest.raises(ValueError):
        xlmr_clf.init_model(None)

    train_df_empty = pd.DataFrame()
    train_df_invalid = pd.DataFrame(
        [
            {"apples": "yes", "fruit": "fruit"},
            {"apples": "yea", "fruit": "fruit"},
            {"apples": "no", "fruit": "fruit"},
            {"apples": "nope", "fruit": "fruit"},
        ]
    )
    assert xlmr_clf.validate(train_df_empty) is False

    xlmr_clf.train(train_df_empty)
    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf.validate(train_df_invalid) is False

    xlmr_clf.train(train_df_invalid)
    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf.inference(["text"])[0].name == "_error_"

    with pytest.raises(ValueError):
        xlmr_clf.save()

    xlmr_clf.model = MockClassifier(const.XLMR_MODEL, const.XLMR_MODEL_TIER)
    with pytest.raises(AttributeError):
        xlmr_clf.inference(["text"])

    if os.path.exists(file_path):
        os.remove(file_path)
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_inference(payload):
    save_module_name = const.XLMR_MODULE
    save_model_name = const.XLMR_MULTI_CLASS_MODEL
    const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"
    directory = "/tmp"
    file_path = os.path.join(directory, const.LABELENCODER_FILE)
    if os.path.exists(file_path):
        os.remove(file_path)

    text = payload.get("input")
    intent = payload["expected"]["label"]

    xlmr_clf = XLMRMultiClass(
        model_dir=directory,
        access=lambda w: (w.input[const.CLASSIFICATION_INPUT],),
        mutate=write_intent_to_workflow,
        debug=False,
    )

    merge_asr_output_plugin = MergeASROutputPlugin(
        access=lambda w: (w.input[const.CLASSIFICATION_INPUT],),
        mutate=update_input,
    )

    workflow = Workflow([merge_asr_output_plugin, xlmr_clf])

    train_df = pd.DataFrame(
        [
            {
                "data": json.dumps([[{"transcript": "yes"}]]),
                "labels": "_confirm_",
            },
            {
                "data": json.dumps([[{"transcript": "yea"}]]),
                "labels": "_confirm_",
            },
            {
                "data": json.dumps([[{"transcript": "no"}]]),
                "labels": "_cancel_",
            },
            {
                "data": json.dumps([[{"transcript": "nope"}]]),
                "labels": "_cancel_",
            },
        ]
    )

    workflow.train(train_df)
    assert isinstance(
        xlmr_clf.model, MockClassifier
    ), "model should be a MockClassifier after training."

    output = workflow.run(input_={const.CLASSIFICATION_INPUT: text})
    assert output[const.INTENTS][0].name == intent
    assert output[const.INTENTS][0].score > 0.9

    if os.path.exists(file_path):
        os.remove(file_path)
    const.XLMR_MODULE = save_module_name
    const.XLMR_MULTI_CLASS_MODEL = save_model_name
