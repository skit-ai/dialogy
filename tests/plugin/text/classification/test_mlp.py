import json
import os
import tempfile
from typing import List

import pandas as pd
import pytest
import sklearn
import joblib

import dialogy.constants as const
from dialogy.plugins import MergeASROutputPlugin, MLPMultiClass
from dialogy.utils import load_file
from dialogy.workflow import Workflow
from tests import load_tests


class MockMLPClassifier:
    def __init__(self, model_dir, args=None, **kwargs):
        self.model_dir = model_dir
        self.args = args or {}
        self.kwargs = kwargs
        if not os.path.isdir(self.model_dir):
            raise OSError("No such directory")

    def inference(self, texts: List[str]):
        return

    def train(self, training_data: pd.DataFrame):
        return


def write_intent_to_workflow(w, v):
    w.output[const.INTENTS] = v


def update_input(w, v):
    w.input[const.CLASSIFICATION_INPUT] = v


def test_mlp_plugin_when_no_mlpmodel_saved():
    mlp_clf = MLPMultiClass(
        model_dir=".",
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    assert isinstance(mlp_clf, MLPMultiClass)
    assert mlp_clf.model_pipeline is None


def test_mlp_plugin_when_mlpmodel_EOFError(capsys):
    _, file_path = tempfile.mkstemp(suffix=".pkl")
    save_mlp_model_file = const.MLPMODEL_FILE
    directory, file_name = os.path.split(file_path)
    const.MLPMODEL_FILE = file_name
    with capsys.disabled():
        mlp_plugin = MLPMultiClass(
            model_dir=directory,
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
            debug=True,
        )
        assert mlp_plugin.model_pipeline is None
    os.remove(file_path)
    const.MLPMODEL_FILE = save_mlp_model_file


def test_mlp_init_mock():
    mlp_clf = MLPMultiClass(
        model_dir=".",
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    mlp_clf.init_model()
    assert isinstance(mlp_clf.model_pipeline, sklearn.pipeline.Pipeline)


def test_mlp_invalid_argsmap():
    with pytest.raises(ValueError):
        MLPMultiClass(
            model_dir=".",
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
            args_map={"invalid": "value"},
        )


def test_mlp_gridsearch_argsmap():
    USE = "use"
    fake_args = {
        const.TRAIN: {
            const.NUM_TRAIN_EPOCHS: 10,
            const.USE_GRIDSEARCH: {
                USE: True,
                const.CV: 2,
                const.VERBOSE_LEVEL: 2,
                const.PARAMS: {
                    "activation": ["relu", "sigmoid"],
                    "hidden_layer_sizes": [(10,), (10, 10), (10, 10, 10)],
                    "ngram_range": [(1, 1), (1, 2), (2, 2)],
                    "max_iter": [10, 100, 1000],
                },
            },
        },
        const.TEST: {},
        const.PRODUCTION: {},
    }

    xlmr_clf = MLPMultiClass(
        model_dir=".",
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
        args_map=fake_args,
    )
    xlmr_clf.init_model()
    assert isinstance(xlmr_clf.model_pipeline, sklearn.model_selection.GridSearchCV)

    fake_invalid_args = {
        const.TRAIN: {
            const.NUM_TRAIN_EPOCHS: 10,
            const.USE_GRIDSEARCH: {
                USE: True,
                const.CV: 2,
                const.VERBOSE_LEVEL: 2,
                const.PARAMS: {
                    "activation": ["relu", "sigmoid"],
                    "hidden_layer_sizes": [(10,), (10, 10), (10, 10, 10)],
                    "ngram_range": [(1, 1), (1, 2), (2, 2)],
                    "iterations": [10, 100, 1000],
                },
            },
        },
        const.TEST: {},
        const.PRODUCTION: {},
    }

    with pytest.raises(ValueError):
        xlmr_clf_invalid = MLPMultiClass(
            model_dir=".",
            access=lambda w: w.input[const.CLASSIFICATION_INPUT],
            mutate=write_intent_to_workflow,
            args_map=fake_invalid_args,
        )
        xlmr_clf_invalid.init_model()


def test_train_mlp_mock():
    directory = "/tmp"
    file_path = os.path.join(directory, const.MLPMODEL_FILE)

    mlp_clf = MLPMultiClass(
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

    mlp_clf.train(train_df)
    assert mlp_clf.labels_num == 2

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the saved mlp model.
    mlp_clf_copy = MLPMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    mlp_clf_copy.load()
    assert isinstance(mlp_clf_copy.model_pipeline, sklearn.pipeline.Pipeline)
    assert mlp_clf_copy.valid_mlpmodel is True
    os.remove(file_path)


def test_train_mlp_gridsearch_mock():
    directory = "/tmp"
    file_path = os.path.join(directory, const.MLPMODEL_FILE)
    USE = "use"
    fake_args = {
        const.TRAIN: {
            const.NUM_TRAIN_EPOCHS: 10,
            const.USE_GRIDSEARCH: {
                USE: True,
                const.CV: 2,
                const.VERBOSE_LEVEL: 2,
                const.PARAMS: {
                    "activation": ["relu", "tanh"],
                    "hidden_layer_sizes": [(1,), (2, 1)],
                    "ngram_range": [(1, 1)],
                    "max_iter": [1, 2],
                },
            },
        },
        const.TEST: {},
        const.PRODUCTION: {},
    }

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
        args_map=fake_args,
    )

    train_df = pd.DataFrame(
        [
            {"data": "yes", "labels": "_confirm_"},
            {"data": "yea", "labels": "_confirm_"},
            {"data": "no", "labels": "_cancel_"},
            {"data": "nope", "labels": "_cancel_"},
        ]
    )

    mlp_clf.train(train_df)
    assert mlp_clf.labels_num == 2

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the saved mlp model.
    mlp_clf_copy = MLPMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    mlp_clf_copy.load()
    assert mlp_clf_copy.valid_mlpmodel is True
    mlp_clf_copy.train(train_df)  # When trying to train an already trained model
    os.remove(file_path)


def test_invalid_operations():
    directory = "/tmp"
    file_path = os.path.join(directory, const.MLPMODEL_FILE)
    if os.path.exists(file_path):
        os.remove(file_path)

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        access=lambda w: w.input[const.CLASSIFICATION_INPUT],
        mutate=write_intent_to_workflow,
    )
    mlp_clf.init_model()

    train_df_empty = pd.DataFrame()
    train_df_invalid = pd.DataFrame(
        [
            {"apples": "yes", "fruit": "fruit"},
            {"apples": "yea", "fruit": "fruit"},
            {"apples": "no", "fruit": "fruit"},
            {"apples": "nope", "fruit": "fruit"},
        ]
    )
    assert mlp_clf.validate(train_df_empty) is False

    mlp_clf.train(train_df_empty)
    assert load_file(file_path, mode="rb", loader=joblib.load) is None
    assert mlp_clf.validate(train_df_invalid) is False

    mlp_clf.train(train_df_invalid)
    assert load_file(file_path, mode="rb", loader=joblib.load) is None
    assert mlp_clf.inference(["text"])[0].name == "_error_"

    with pytest.raises(ValueError):
        mlp_clf.save()

    mlp_clf.model_pipeline = MockMLPClassifier(directory)
    with pytest.raises(AttributeError):
        mlp_clf.inference(["text"])

    assert mlp_clf.inference([])[0].name == "_error_"

    mlp_clf.model_pipeline = None
    # with pytest.raises(AttributeError):
    assert mlp_clf.inference(["text"])[0].name == "_error_"

    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.mark.parametrize("payload", load_tests("mlp_cases", __file__))
def test_inference(payload):
    # save_module_name = const.XLMR_MODULE
    # save_model_name = const.XLMR_MULTI_CLASS_MODEL
    # const.XLMR_MODULE = "tests.plugin.text.classification.test_xlmr"
    # const.XLMR_MULTI_CLASS_MODEL = "MockClassifier"

    directory = "/tmp"
    file_path = os.path.join(directory, const.MLPMODEL_FILE)
    if os.path.exists(file_path):
        os.remove(file_path)

    USE = "use"
    fake_args = {
        const.TRAIN: {
            const.NUM_TRAIN_EPOCHS: 5,
            const.USE_GRIDSEARCH: {
                USE: False,
                const.CV: 2,
                const.VERBOSE_LEVEL: 2,
                const.PARAMS: {
                    "activation": ["relu", "tanh"],
                    "hidden_layer_sizes": [(10,), (2, 2)],
                    "ngram_range": [(1, 1), (1, 2)],
                    "max_iter": [20, 2],
                },
            },
        },
        const.TEST: {},
        const.PRODUCTION: {},
    }

    text = payload.get("input")
    intent = payload["expected"]["label"]

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        access=lambda w: (w.input[const.CLASSIFICATION_INPUT],),
        mutate=write_intent_to_workflow,
        args_map=fake_args,
        debug=True,
    )

    merge_asr_output_plugin = MergeASROutputPlugin(
        access=lambda w: (w.input[const.CLASSIFICATION_INPUT],),
        mutate=update_input,
    )

    workflow = Workflow([merge_asr_output_plugin, mlp_clf])

    train_df = pd.DataFrame(
        [
            {
                "data": json.dumps([[{"transcript": "yes"}]]),
                "labels": "_confirm_",
            },
            {
                "data": json.dumps([[{"transcript": "ye"}]]),
                "labels": "_confirm_",
            },
            {
                "data": json.dumps([[{"transcript": "<s> yes </s> <s> ye </s>"}]]),
                "labels": "_confirm_",
            },
            {
                "data": json.dumps([[{"transcript": "no"}]]),
                "labels": "_cancel_",
            },
            {
                "data": json.dumps([[{"transcript": "new"}]]),
                "labels": "_cancel_",
            },
            {
                "data": json.dumps([[{"transcript": "<s> new </s> <s> no </s>"}]]),
                "labels": "_cancel_",
            },
        ]
    )

    workflow.train(train_df)
    output = workflow.run(input_={const.CLASSIFICATION_INPUT: text})
    assert output[const.INTENTS][0].name == intent
    assert output[const.INTENTS][0].score > 0.5
    if os.path.exists(file_path):
        os.remove(file_path)
