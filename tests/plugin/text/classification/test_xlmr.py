import json
import os
import pickle
import tempfile
from typing import List, Optional

import numpy as np
import pandas as pd
import pytest

import dialogy.constants as const
from dialogy.base import Input
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


def test_xlmr_plugin_no_module_error(mocker):
    mocker.patch.object(const, "XLMR_MODULE", "invalid_module")

    with pytest.raises(ModuleNotFoundError):
        XLMRMultiClass(model_dir=".", dest="output.intents", debug=False)


def test_xlmr_plugin_when_no_labelencoder_saved(mocker):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")

    xlmr_clf = XLMRMultiClass(model_dir=".", dest="output.intents", debug=False)
    assert isinstance(xlmr_clf, XLMRMultiClass)
    assert xlmr_clf.model is None


def test_xlmr_plugin_when_labelencoder_EOFError(capsys, mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")

    _, file_path = tempfile.mkstemp(suffix=".pkl")
    save_label_encoder_file = const.LABELENCODER_FILE
    directory, file_name = os.path.split(file_path)
    const.LABELENCODER_FILE = file_name

    with capsys.disabled():
        xlmr_plugin = XLMRMultiClass(
            model_dir=directory,
            dest="output.intents",
            debug=False,
        )
        assert xlmr_plugin.model is None
    os.remove(file_path)
    const.LABELENCODER_FILE = save_label_encoder_file


def test_xlmr_init_mock(mocker):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")

    xlmr_clf = XLMRMultiClass(model_dir=".", dest="output.intents", debug=False)
    xlmr_clf.init_model(5)
    assert xlmr_clf.model is not None


def test_xlmr_init_mock(mocker):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")

    with pytest.raises(ValueError):
        XLMRMultiClass(
            model_dir=".",
            dest="output.intents",
            debug=False,
            args_map={"invalid": "value"},
        )


def test_train_xlmr_mock(mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")

    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join("labelencoder.pkl")
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    xlmr_clf = XLMRMultiClass(model_dir=directory, dest="output.intents", debug=False)

    xlmr_clf_state = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
        use_state=True,
    )

    train_df = pd.DataFrame(
        [
            {"data": "yes", "labels": "_confirm_"},
            {"data": "yea", "labels": "_confirm_"},
            {"data": "no", "labels": "_cancel_"},
            {"data": "nope", "labels": "_cancel_"},
        ]
    )

    train_df_state = pd.DataFrame(
        [
            {"data": "yes", "labels": "_confirm_", "state": "state1"},
            {"data": "yea", "labels": "_confirm_", "state": "state2"},
            {"data": "no", "labels": "_cancel_", "state": "state3"},
            {"data": "nope", "labels": "_cancel_", "state": "state4"},
        ]
    )

    xlmr_clf.train(train_df)
    xlmr_clf_state.train(train_df_state)

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the labelencoder saved.
    xlmr_clf_copy = XLMRMultiClass(
        model_dir=directory, dest="output.intents", debug=False
    )

    assert len(xlmr_clf_copy.labelencoder.classes_) == 2


def test_invalid_operations(mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join("labelencoder.pkl")
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    xlmr_clf = XLMRMultiClass(model_dir=directory, dest="output.intents", debug=False)

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


def test_invalid_operations_with_state(mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join("labelencoder.pkl")
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    xlmr_clf_state = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
        use_state=True,
    )

    with pytest.raises(ValueError):
        xlmr_clf_state.init_model(None)

    train_df_empty = pd.DataFrame()
    train_df_invalid = pd.DataFrame(
        [
            {"apples": "yes", "fruit": "fruit"},
            {"apples": "yea", "fruit": "fruit"},
            {"apples": "no", "fruit": "fruit"},
            {"apples": "nope", "fruit": "fruit"},
        ]
    )
    assert xlmr_clf_state.validate(train_df_empty) is False

    xlmr_clf_state.train(train_df_empty)

    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf_state.validate(train_df_invalid) is False

    xlmr_clf_state.train(train_df_invalid)
    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf_state.inference(["text"])[0].name == "_error_"

    xlmr_clf_state.model = MockClassifier(const.XLMR_MODEL, const.XLMR_MODEL_TIER)
    with pytest.raises(ValueError):
        xlmr_clf_state.inference(["text"])

    with pytest.raises(ValueError):
        xlmr_clf_state.save()


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_inference(payload, mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join(const.LABELENCODER_FILE)
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    transcripts = payload.get("input")
    intent = payload["expected"]["label"]

    xlmr_clf = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
        purpose=const.TEST,
        args_map={
            const.TEST: {const.MODEL_CALIBRATION: True},
            const.TRAIN: {},
            const.PRODUCTION: {},
        },
    )

    merge_asr_output_plugin = MergeASROutputPlugin(
        dest="input.clf_feature", debug=False
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

    _, output = workflow.run(
        Input(utterances=[[{"transcript": transcript} for transcript in transcripts]])
    )
    output = output.dict()

    assert output[const.INTENTS][0]["name"] == intent
    assert output[const.INTENTS][0]["score"] > 0.9


def test_train_xlmr_prompt_1(mocker, tmpdir):
    """
    Code to test xlmr workflow, with the following parameters:
    use_state: False
    use_prompt: True
    train_using_all_prompts: False
    """
    # print("\nRunning test_train_xlmr_prompt_1")

    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join(const.LABELENCODER_FILE)
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    prompts_map = {
        "en": {
            "nls_label1": "prompt1",
            "nls_label2": "prompt2",
            "nls_label3": "prompt3",
        },
        "hi": {"nls_label1": "prompt4", "nls_label2": "prompt5"},
    }

    xlmr_clf_prompt = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
        prompts_map=prompts_map,
        use_state=False,
        use_prompt=True,
    )

    train_df_prompt = pd.DataFrame(
        [
            {
                "data": "yes",
                "labels": "_confirm_",
                "nls_label": "nls_label1",
                "lang": "lang1",
            },
            {
                "data": "yea",
                "labels": "_confirm_",
                "nls_label": "nls_label2",
                "lang": "lang1",
            },
            {
                "data": "no",
                "labels": "_cancel_",
                "nls_label": "nls_label3",
                "lang": "lang2",
            },
            {
                "data": "nope",
                "labels": "_cancel_",
                "nls_label": "nls_label1",
                "lang": "lang2",
            },
        ]
    )

    try:
        xlmr_clf_prompt.train(train_df_prompt)
    except ValueError:
        pass

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the labelencoder saved.
    xlmr_clf_copy = XLMRMultiClass(
        model_dir=directory, dest="output.intents", debug=False
    )

    assert len(xlmr_clf_copy.labelencoder.classes_) == 2


def test_train_xlmr_prompt_2(mocker, tmpdir):
    """
    Code to test xlmr workflow, with the following parameters:
    use_state: True
    use_prompt: True
    train_using_all_prompts: True
    """
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join(const.LABELENCODER_FILE)
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    prompts_map = {
        "en": {
            "nls_label1": "prompt1",
            "nls_label2": "prompt2",
            "nls_label3": "prompt3",
        },
        "hi": {"nls_label1": "prompt4", "nls_label2": "prompt5"},
    }

    xlmr_clf_prompt = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=True,
        prompts_map=prompts_map,
        use_state=True,
        use_prompt=True,
    )

    train_df_prompt = pd.DataFrame(
        [
            {
                "data": "yes",
                "labels": "_confirm_",
                "state": "state1",
                "lang": "lang1",
                "nls_label": "nls_label1",
            },
            {
                "data": "yea",
                "labels": "_confirm_",
                "state": "state2",
                "lang": "lang1",
                "nls_label": "nls_label2",
            },
            {
                "data": "no",
                "labels": "_cancel_",
                "state": "state1",
                "lang": "lang2",
                "nls_label": "nls_label3",
            },
            {
                "data": "nope",
                "labels": "_cancel_",
                "state": "state3",
                "lang": "lang3",
                "nls_label": "nls_label4",
            },
        ]
    )

    try:
        xlmr_clf_prompt.train(train_df_prompt)
    except ValueError:
        pass

    assert (
        len(
            xlmr_clf_prompt.inference(
                texts=["yes"], lang="lang1", state="state1", nls_label="nls_label1"
            )
        )
        > 0
    )

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the labelencoder saved.
    xlmr_clf_copy = XLMRMultiClass(
        model_dir=directory, dest="output.intents", debug=False
    )

    assert len(xlmr_clf_copy.labelencoder.classes_) == 2


def test_invalid_operations_with_prompt(mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join(const.LABELENCODER_FILE)
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    xlmr_clf_prompt = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=True,
        use_state=False,
        use_prompt=True,
        prompts_map={},
    )

    with pytest.raises(ValueError):
        xlmr_clf_prompt.init_model(None)

    train_df_empty = pd.DataFrame()
    train_df_invalid = pd.DataFrame(
        [
            {"apples": "yes", "fruit": "fruit"},
            {"apples": "yea", "fruit": "fruit"},
            {"apples": "no", "fruit": "fruit"},
            {"apples": "nope", "fruit": "fruit"},
        ]
    )

    assert xlmr_clf_prompt.validate(train_df_empty) is False

    xlmr_clf_prompt.train(train_df_empty)

    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf_prompt.validate(train_df_invalid) is False

    xlmr_clf_prompt.train(train_df_invalid)
    assert load_file(file_path, mode="rb", loader=pickle.load) is None
    assert xlmr_clf_prompt.inference(["text"])[0].name == "_error_"

    xlmr_clf_prompt.model = MockClassifier(const.XLMR_MODEL, const.XLMR_MODEL_TIER)

    with pytest.raises(ValueError):
        xlmr_clf_prompt.inference(texts=["text"])

    with pytest.raises(ValueError):
        xlmr_clf_prompt.inference(texts=["text"], lang="hi", nls_label=None)

    with pytest.raises(ValueError):
        xlmr_clf_prompt.inference(texts=["text"], lang=None, nls_label="nls_label1")

    with pytest.raises(ValueError):
        xlmr_clf_prompt.save()


@pytest.mark.parametrize("payload", load_tests("cases", __file__))
def test_inference_with_prompt_1(payload, mocker, tmpdir):
    mocker.patch.object(
        const, "XLMR_MODULE", "tests.plugin.text.classification.test_xlmr"
    )
    mocker.patch.object(const, "XLMR_MULTI_CLASS_MODEL", "MockClassifier")
    directory = "/tmp"
    file_path = tmpdir.mkdir(directory).join(const.LABELENCODER_FILE)
    mocker.patch.object(const, "LABELENCODER_FILE", file_path)

    prompts_map = {
        "en": {
            "nls_label1": "prompt1",
            "nls_label2": "prompt2",
            "nls_label3": "prompt3",
        },
        "hi": {"nls_label1": "prompt4", "nls_label2": "prompt5"},
    }

    train_df_prompt = pd.DataFrame(
        [
            {
                "data": "yes",
                "labels": "_confirm_",
                "state": "state1",
                "lang": "lang1",
                "nls_label": "nls_label1",
            },
            {
                "data": "yea",
                "labels": "_confirm_",
                "state": "state2",
                "lang": "lang1",
                "nls_label": "nls_label2",
            },
            {
                "data": "no",
                "labels": "_cancel_",
                "state": "state1",
                "lang": "lang2",
                "nls_label": "nls_label3",
            },
            {
                "data": "nope",
                "labels": "_cancel_",
                "state": "state3",
                "lang": "lang3",
                "nls_label": "nls_label4",
            },
        ]
    )

    xlmr_clf_prompt = XLMRMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=True,
        prompts_map=prompts_map,
        use_state=False,
        use_prompt=True,
    )

    merge_asr_output_plugin = MergeASROutputPlugin(
        dest="input.clf_feature", debug=False
    )
    try:
        xlmr_clf_prompt.train(train_df_prompt)
    except ValueError:
        pass

    train_df_empty = pd.DataFrame()
    train_df_invalid = pd.DataFrame(
        [
            {"apples": "yes", "fruit": "fruit"},
            {"apples": "yea", "fruit": "fruit"},
            {"apples": "no", "fruit": "fruit"},
            {"apples": "nope", "fruit": "fruit"},
        ]
    )

    assert xlmr_clf_prompt.validate(train_df_empty) is False
    assert xlmr_clf_prompt.validate(train_df_invalid) is False

    with pytest.raises(ValueError):
        xlmr_clf_prompt.inference(texts=["text"], lang="hi", nls_label=None)

    with pytest.raises(ValueError):
        xlmr_clf_prompt.inference(texts=["text"], lang=None, nls_label="nls_label1")

    assert (
        len(
            xlmr_clf_prompt.inference(
                texts=["yes"], lang="lang1", nls_label="nls_label1"
            )
        )
        > 0
    )

    assert (
        len(
            xlmr_clf_prompt.inference(
                texts=["yes"], lang="unsupported_lang", nls_label="nls_label1"
            )
        )
        > 0
    )

    assert (
        len(
            xlmr_clf_prompt.inference(
                texts=["yes"], lang="lang1", nls_label="unsupported_nls_label"
            )
        )
        > 0
    )

    assert (
        len(
            xlmr_clf_prompt.inference(
                texts=["yes"],
                lang="unsupported_lang",
                nls_label="unsupported_nls_label",
            )
        )
        > 0
    )
