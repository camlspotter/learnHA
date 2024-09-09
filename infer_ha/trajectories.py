import csv
import numpy as np
from numpy.typing import NDArray
from typing import Optional, TypeVar, Callable, Iterator
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

Trajectory = tuple[ np.ndarray,  # time part of timeseries. 1D array
                    np.ndarray ] # values part of timeseries 2D array

# config is required to carry np.ndarray in pydantic's dataclass
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Trajectories:
    trajectories : list[ Trajectory ]
    stepsize : float

def parse_trajectories(path : str) -> Trajectories:
    '''
    Load trajectories from a tsv file.
    
    - No check of stepsize uniqueness
    '''
    with open(path, 'r') as ic:
        reader = csv.reader(ic, delimiter='\t')

        tvs_list : list[tuple[float, list[float]]] = \
            list(map(lambda ss: (float(ss[0]), [float(s) for s in ss[1:]]), reader))

        zero_poses : list[int] = [ i for (i, (t,_vs)) in enumerate(tvs_list) if t == 0.0 ]
        ranges : list[tuple[int,int]] = \
            [ (zero_poses[i], zero_poses[i+1] if i + 1 < len(zero_poses) else len(tvs_list))
              for (i,_) in enumerate(zero_poses) ]

        tvs_group : list[list[tuple[float, list[float]]]] = [ tvs_list[start:end] for (start, end) in ranges ]

        trajectories : list[Trajectory] = [ ( np.array([t for (t, _) in tvs]),
                                               np.array([vs for (_, vs) in tvs]) )
                                             for tvs in tvs_group ]

        stepsize = tvs_group[0][1][0] - tvs_group[0][0][0] # diff of the first 2 times in the first tvs

        return Trajectories(trajectories, stepsize)

def preprocess_trajectories(list_of_trajectories : list[Trajectory]) -> tuple[ NDArray[np.float64],
                                                                               NDArray[np.float64],
                                                                               list[tuple[int, int]] ]:
    '''
    This function performs the actual conversion of the list of trajectories into a single trajectory.

    :param list_of_trajectories: Each element of the list is a trajectory.
                                 A trajectory is a 2-tuple of (time, vector), where
    :time: is a list having a single item. The item is the sampling time, stored as a numpy.ndarray having structure as
           (rows, ) where rows is the number of sample points. The dimension cols is empty meaning a single dim array.
    :vector: is a list having a single item. The item is a numpy.ndarray with (rows,cols), rows indicates the number of
           points and cols as the system's dimension. The dimension is the total number of variables in the trajectories
           including both input and output variables.

    :return: the value pair (time and vector) where
        t_list: a single-item list whose item is a numpy.ndarray containing time-values as a concatenated list
        y_list: a single-item list whose item is a numpy.ndarray containing vector of values (of input and output) as a
                concatenated list of trajectories.
        ranges: the ranges of the Trajectories in the lists.
    '''

    sizes = [ len(ts) for traj in list_of_trajectories for ts in [traj[0]] ]

    position : list[tuple[int,int]] = []
    for (i,size) in enumerate(sizes):
        last_position = position[i-1][1] if i > 0 else -1
        position.append((last_position + 1, last_position + size))

    # XXX Why does this returns singleton lists?
    t = np.concatenate([ traj[0] for traj in list_of_trajectories ])
    y = np.vstack([ traj[1] for traj in list_of_trajectories ])

    return t, y, position
