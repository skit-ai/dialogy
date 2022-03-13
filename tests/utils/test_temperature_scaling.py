import os

import numpy as np
import torch

import dialogy.constants as const
from dialogy.utils.temperature_scaling import (
    T_scaling,
    calc_bins,
    fit_ts_parameter,
    get_metrics,
    save_reliability_graph,
)

logits = np.array([[-1.34, 5.33, 10.1, 0.56], [-1.34, 0.33, -10.1, 0.86]])
preds = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
labels_oneh = np.array([[0, 1, 0, 0], [0, 0, 0, 1]])
labels_list = np.array([1, 3])


def test_calc_bins():
    res = calc_bins(preds, labels_oneh)
    assert len(res) == 5
    assert len(res[0]) == 10
    assert res[1].shape == (2, 4)
    assert len(res[2]) == 10
    assert len(res[3]) == 10
    assert len(res[4]) == 10


def test_get_metrics():
    ece, mce = get_metrics(preds, labels_oneh)
    assert isinstance(ece, float)
    assert isinstance(mce, float)


def test_save_reliability_graph():
    prefix = "test"
    temp_dir = "/tmp"
    graph_name = "reliability_graph"
    full_path = os.path.join(temp_dir, f"{prefix}_{graph_name}.png")
    save_reliability_graph(preds, labels_oneh, temp_dir, prefix)
    assert os.path.exists(full_path)
    os.remove(full_path)


def test_T_scaling():
    fake_temp = 1.1
    logits_tensor = torch.from_numpy(logits)
    ans = logits_tensor / fake_temp
    res = T_scaling(logits_tensor, fake_temp)
    assert torch.all(torch.eq(ans, res))


def test_fit_ts_parameter():
    res1 = fit_ts_parameter(logits, labels_list, lr=0, max_iter=1)
    res2 = fit_ts_parameter(logits, labels_list, lr=0.1, max_iter=1)
    assert isinstance(res1, float)
    assert isinstance(res2, float)
    assert res1 != res2
