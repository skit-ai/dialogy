import os.path

import pandas as pd
import pytest

from dialogy.plugins import LabelDenoiserPlugin


@pytest.mark.parametrize(
    "alternatives, tags, drop, discard_size",
    [
        (
            [
                '[[{"transcript": "hello"}]]',
                '[[{"transcript": "hello"}]]',
                '[[{"transcript": "bye"}]]',
            ],
            ["x1", "x2", "x3"],
            True,
            2,
        ),
        (
            [
                '[[{"transcript": "hello"}]]',
                '[[{"transcript": "hello"}]]',
                '[[{"transcript": "bye"}]]',
            ],
            ["x1", "x2", "x3"],
            False,
            0,
        ),
    ],
)
def test_drop_conflicting_labels(alternatives, tags, drop, discard_size, tmp_path) -> None:
    label_denoiser_plugin = LabelDenoiserPlugin(
        discarded_output_path=tmp_path, use_transform=True, drop_conflicting_labels=drop
    )

    training_data = pd.DataFrame({"alternatives": alternatives, "tag": tags})

    training_data_ = label_denoiser_plugin.transform(training_data)

    assert len(training_data) - len(training_data_) == discard_size
    assert os.path.exists(os.path.join(tmp_path, "discarded_train_data.csv"))
