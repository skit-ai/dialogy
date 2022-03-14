import os
from typing import Any, Tuple

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import torch
import torch.nn as nn
import torch.optim as optim
from torch import Tensor

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def calc_bins(
    preds: npt.NDArray[np.float64], labels_oneh: npt.NDArray[np.float64]
) -> Any:
    # Assign each prediction to a bin
    num_bins = 10
    bins = np.linspace(0.1, 1, num_bins)
    binned = np.digitize(preds, bins)

    # Save the accuracy, confidence and size of each bin
    bin_accs = np.zeros(num_bins)
    bin_confs = np.zeros(num_bins)
    bin_sizes = np.zeros(num_bins)

    for bin in range(num_bins):
        bin_sizes[bin] = len(preds[binned == bin])
        if bin_sizes[bin] > 0:
            bin_accs[bin] = (labels_oneh[binned == bin]).sum() / bin_sizes[bin]
            bin_confs[bin] = (preds[binned == bin]).sum() / bin_sizes[bin]

    return bins, binned, bin_accs, bin_confs, bin_sizes


def get_metrics(
    preds: npt.NDArray[np.float64], labels_oneh: npt.NDArray[np.float64]
) -> Tuple[float, float]:
    ECE = 0
    MCE = 0
    bins, _, bin_accs, bin_confs, bin_sizes = calc_bins(preds, labels_oneh)

    for i in range(len(bins)):
        abs_conf_dif = abs(bin_accs[i] - bin_confs[i])
        ECE += (bin_sizes[i] / sum(bin_sizes)) * abs_conf_dif
        MCE = max(MCE, abs_conf_dif)

    return ECE, MCE


def save_reliability_graph(
    preds: npt.NDArray[np.float64],
    labels_oneh: npt.NDArray[np.float64],
    dir_path: str,
    prefix: str,
) -> None:
    ECE, MCE = get_metrics(preds, labels_oneh)

    bins, _, bin_accs, _, _ = calc_bins(preds, labels_oneh)

    fig = plt.figure(figsize=(8, 8))
    ax = fig.gca()

    # x/y limits
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1)

    # x/y labels
    plt.xlabel("Confidence")
    plt.ylabel("Accuracy")

    # Create grid
    ax.set_axisbelow(True)
    ax.grid(color="gray", linestyle="dashed")

    # Error bars
    plt.bar(bins, bins, width=0.1, alpha=0.3, edgecolor="black", color="r", hatch="\\")

    # Draw bars and identity line
    plt.bar(bins, bin_accs, width=0.1, alpha=1, edgecolor="black", color="b")
    plt.plot([0, 1], [0, 1], "--", color="gray", linewidth=2)

    # Equally spaced axes
    plt.gca().set_aspect("equal", adjustable="box")

    # ECE and MCE legend
    ECE_patch = mpatches.Patch(color="green", label="ECE = {:.2f}%".format(ECE * 100))
    MCE_patch = mpatches.Patch(color="red", label="MCE = {:.2f}%".format(MCE * 100))

    plt.legend(handles=[ECE_patch, MCE_patch])

    plt.savefig(
        os.path.join(dir_path, f"{prefix}_reliability_graph.png"), bbox_inches="tight"
    )


def T_scaling(logits: Tensor, temperature: Tensor) -> Tensor:
    return torch.div(logits, temperature)


def fit_ts_parameter(
    logits_list: npt.NDArray[np.float64],
    labels_list: npt.NDArray[np.int64],
    lr: float = 0.001,
    max_iter: int = 10000,
    device: torch.device = DEVICE,
) -> float:
    logits_tensor = torch.from_numpy(logits_list).to(device)
    labels_tensor = torch.from_numpy(labels_list).to(device)
    temperature = nn.Parameter(torch.ones(1).to(device))
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.LBFGS(
        [temperature], lr=lr, max_iter=max_iter, line_search_fn="strong_wolfe"
    )

    import time

    def _eval() -> Any:
        loss = criterion(T_scaling(logits_tensor, temperature), labels_tensor)
        loss.backward()
        return loss

    optimizer.step(_eval)
    return round(temperature.item(), 4)
