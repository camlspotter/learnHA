from typing import Optional
import numpy as np
import matplotlib.pyplot as plt
from hybridlearner.types import MATRIX


def plot_timeseries(
    fn: str,
    ts: MATRIX,  # 1D times
    vs: MATRIX,  # 2D values
) -> None:
    plt.plot(ts, vs)
    plt.grid()
    plt.savefig(fn)


def plot_timeseries_multi(
    fn: str,
    title: str,
    header: Optional[list[str]],
    tv_list: list[
        tuple[
            MATRIX,  # 1D times
            MATRIX,  # 2D values
        ]
    ],
) -> None:
    """
    Plot multiple timeseries side by side, by shifting them horizontally
    to avoid overwraps.
    """
    offset = 0.0

    plt.clf()

    fig, subs = plt.subplots(len(tv_list), 1, figsize=(6, 3 * len(tv_list)))
    fig.tight_layout(rect=[0, 0, 1, 0.96], pad=2)  # type: ignore
    fig.suptitle(title)

    for i, (ts, vs) in enumerate(tv_list):
        subs[i].set_title(f'Trajectory {i+1}')
        subs[i].plot(ts, vs)

    # plt.grid()
    plt.savefig(fn)
