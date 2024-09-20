import os
import numpy as np
import matplotlib.pyplot as plt
from hybridlearner.types import MATRIX

def plot_timeseries(fn : str,
                    ts : MATRIX, # 1D times
                    vs : MATRIX, # 2D values
                    ) -> None:
    plt.plot(ts, vs)
    plt.grid()
    plt.savefig(fn)

def plot_timeseries_multi(fn : str,
                          title : str,
                          tv_list : list[tuple[MATRIX, # 1D times
                                               MATRIX]], # 2D values
                          space : float
                          ) -> None:
    """
    Plot multiple timeseries side by side, by shifting them horizontally
    to avoid overwraps.
    """
    offset = 0.0

    plt.clf()
    plt.title(title)
    for (i, (ts,vs)) in enumerate(tv_list):
        # map is not accepted by matplotlib
        ts_shifted = np.array(list(map(lambda t: t + offset, ts)))
        # print(list(ts_shifted), list(vs))
        plt.plot(ts_shifted, vs)
        offset += ts[-1] - ts[0] + space

    # plt.grid()
    plt.savefig(fn)
