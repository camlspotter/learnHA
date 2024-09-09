"""
This module is used to parse the list of trajectories structure to construct structures suitable for our algorithm.
"""
import numpy as np
from numpy.typing import NDArray
from infer_ha.trajectories import Trajectory, Trajectories

def preprocess_trajectories(list_of_trajectories : list[Trajectory]) -> tuple[ list[NDArray[np.float64]],
                                                                               list[NDArray[np.float64]],
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

    sizes = [ len(ts) for traj in list_of_trajectories for ts in traj[0] ]

    position : list[tuple[int,int]] = []
    for (i,size) in enumerate(sizes):
        last_position = position[i-1][1] if i > 0 else -1
        position.append((last_position + 1, last_position + size))

    # XXX Why does this returns singleton lists?
    t_list = [np.concatenate([ ts for traj in list_of_trajectories for ts in traj[0] ])]
    y_list = [np.vstack([ ys for traj in list_of_trajectories for ys in traj[1] ])]

    return t_list, y_list, position
