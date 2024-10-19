from io import TextIOWrapper
import csv
import numpy as np
from numpy.typing import NDArray
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

from hybridlearner.types import Span

# Timeseries.
#
# The first element of the tuple is a 1D array of timestamps. The timestamps
# are assumed to be an arithmetic sequence starts from 0.
#
# The second element of the tuple is a 2D matrix of values.  Its number of
# the columns must be equal to the length of the timestamp array.

Trajectory = tuple[
    np.ndarray,  # time part of timeseries. 1D array
    np.ndarray,  # values part of timeseries 2D array
]

# Trajectories
#
# Trajectories is a set of Trajectory.  All the trajectories must share
# the same timestamp gap, here called stepsize.


def trajectory_stepsize(tr: Trajectory) -> float:
    # diff of the first 2 times in the first tvs
    times = tr[0]
    return times[1] - times[0]


def write_trajectory(oc: TextIOWrapper, traj: Trajectory) -> None:
    np.savetxt(oc, np.column_stack(traj), delimiter='\t', fmt='%.16g')


Trajectories = list[Trajectory]


def write_trajectories(oc: TextIOWrapper, trajs: Trajectories) -> None:
    for traj in trajs:
        write_trajectory(oc, traj)


def load_trajectories(path: str) -> Trajectories:
    """
    Load trajectories from a tsv file.

    - No check of stepsize uniqueness
    """
    with open(path, 'r') as ic:
        reader = csv.reader(ic, delimiter='\t')

        tvs_list: list[tuple[float, list[float]]] = list(
            map(lambda ss: (float(ss[0]), [float(s) for s in ss[1:]]), reader)
        )

        zero_poses: list[int] = [i for (i, (t, _vs)) in enumerate(tvs_list) if t == 0.0]
        ranges: list[tuple[int, int]] = [
            (
                zero_poses[i],
                zero_poses[i + 1] if i + 1 < len(zero_poses) else len(tvs_list),
            )
            for (i, _) in enumerate(zero_poses)
        ]

        tvs_group: list[list[tuple[float, list[float]]]] = [
            tvs_list[start:end] for (start, end) in ranges
        ]

        trajectories: list[Trajectory] = [
            (np.array([t for (t, _) in tvs]), np.array([vs for (_, vs) in tvs]))
            for tvs in tvs_group
        ]

        return trajectories


def load_trajectories_files(paths: list[str]) -> Trajectories:
    """
    Load trajectories from tsv files.

    - No check of stepsize uniqueness
    """
    trs_list = [load_trajectories(path) for path in paths]

    stepsize = trajectory_stepsize(trs_list[0][0])
    nvars = trs_list[0][0][1].shape[1]  # 0th trajectory, 0th sample, value

    if not all(lambda trs: trajectory_stepsize(trs) == stepsize for trs in trs_list):
        assert False, "Trajectories files must have a unique stepsize"

    if not all(lambda trs: trs[0][1].shape[1] == nvars for trs in trs_list):
        assert False, "Trajectories files must have the same number of variables"

    return [tr for trs in trs_list for tr in trs]


def preprocess_trajectories(
    list_of_trajectories: Trajectories,
) -> tuple[NDArray[np.float64], NDArray[np.float64], list[Span]]:
    '''
    Concatenate the trajectories.

    :param list_of_trajectories: a list of trajectories.  They must have the same timestamp gap.

    :return: the value pair (time and vector) where
        t: a numpy.ndarray containing time-values as a concatenated list
        y: a numpy.ndarray containing vector of values (of input and output) as a concatenated list of trajectories.
        ranges: the ranges of the Trajectories in the lists.
    '''

    sizes = [len(ts) for traj in list_of_trajectories for ts in [traj[0]]]

    position: list[Span] = []
    for i, size in enumerate(sizes):
        last_position = position[i - 1].end if i > 0 else -1
        position.append(Span(last_position + 1, last_position + size))

    # XXX Why does this returns singleton lists?
    t = np.concatenate([traj[0] for traj in list_of_trajectories])
    y = np.vstack([traj[1] for traj in list_of_trajectories])

    return t, y, position
