import json
import os
from typing import List

import joblib
import pandas as pd
import pytest
import sklearn
from sklearn.model_selection import GridSearchCV

import dialogy.constants as const
from dialogy.base import Input
from dialogy.plugins.registry import MergeASROutputPlugin, MLPMultiClass
from dialogy.utils import load_file
from dialogy.workflow import Workflow
from tests import load_tests


class MockMLPClassifier:
    def __init__(self, model_dir, args=None, **kwargs):
        super().__init__(**kwargs)
        self.model_dir = model_dir
        self.args = args or {}
        self.kwargs = kwargs
        if not os.path.isdir(self.model_dir):
            raise OSError("No such directory")

    def inference(self, texts: List[str]):
        return

    def train(self, training_data: pd.DataFrame):
        return


class MockGridSearchCV:
    def __init__(self, *args, **kwargs):
        self.best_params_ = {}

    def fit(self, X, y):
        self.classes_ = []


def test_mlp_plugin_when_no_mlpmodel_saved():
    mlp_clf = MLPMultiClass(model_dir=".", dest="output.intents")
    assert isinstance(mlp_clf, MLPMultiClass)
    assert mlp_clf.model_pipeline is None


def test_mlp_plugin_when_mlpmodel_EOFError(capsys, tmpdir):
    directory = tmpdir.mkdir("mlp_plugin")
    with capsys.disabled():
        mlp_plugin = MLPMultiClass(
            model_dir=directory,
            dest="output.intents",
            debug=False,
        )
        assert mlp_plugin.model_pipeline is None


def test_mlp_init_mock():
    mlp_clf = MLPMultiClass(
        model_dir=".",
        dest="output.intents",
        debug=False,
    )
    mlp_clf.init_model()
    assert isinstance(mlp_clf.model_pipeline, sklearn.pipeline.Pipeline)


def test_mlp_invalid_argsmap():
    with pytest.raises(ValueError):
        MLPMultiClass(
            model_dir=".",
            dest="output.intents",
            debug=False,
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
        dest="output.intents",
        debug=False,
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
            dest="output.intents",
            debug=False,
            args_map=fake_invalid_args,
        )
        xlmr_clf_invalid.init_model()


def test_train_mlp_mock(tmpdir):
    directory = tmpdir.mkdir("mlp_plugin")
    file_path = os.path.join(directory, const.MLPMODEL_FILE)

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
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
        dest="output.intents",
        debug=False,
    )
    mlp_clf_copy.load()
    assert isinstance(mlp_clf_copy.model_pipeline, sklearn.pipeline.Pipeline)
    assert mlp_clf_copy.valid_mlpmodel is True


def test_train_mlp_gridsearch_mock(tmpdir, monkeypatch, mocker):
    directory = tmpdir.mkdir("mlp_plugin")
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
        dest="output.intents",
        debug=False,
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

    mlp_clf.train(train_df, param_search=MockGridSearchCV)
    assert mlp_clf.labels_num == 2

    # This copy loads from the same directory that was trained previously.
    # So this instance would have read the saved mlp model.
    mlp_clf_copy = MLPMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
    )
    mlp_clf_copy.load()
    assert mlp_clf_copy.valid_mlpmodel is True


def test_invalid_operations(tmpdir):
    directory = tmpdir.mkdir("mlp_plugin")
    file_path = directory.join(const.MLPMODEL_FILE)

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        dest="output.intents",
        debug=False,
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
    assert mlp_clf.inference(["text"])[0].name == "_error_"


@pytest.mark.parametrize("payload", load_tests("mlp_cases", __file__))
def test_inference(payload, tmpdir):
    directory = tmpdir.mkdir("mlp_plugin")
    file_path = directory.join(const.MLPMODEL_FILE)

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

    transcripts = payload.get("input")
    intent = payload["expected"]["label"]

    mlp_clf = MLPMultiClass(
        model_dir=directory,
        dest="output.intents",
        args_map=fake_args,
        debug=False,
    )

    merge_asr_output_plugin = MergeASROutputPlugin(
        dest="input.clf_feature",
        debug=False,
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
    _, output = workflow.run(
        Input(utterances=[[{"transcript": transcript} for transcript in transcripts]])
    )
    assert output.intents[0].name == intent
    assert output.intents[0].score > 0.5
