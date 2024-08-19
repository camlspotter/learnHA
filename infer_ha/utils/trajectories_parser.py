"""
This module is used to parse the list of trajectories structure to construct structures suitable for our algorithm.
"""
import numpy as np
from numpy.typing import NDArray
from infer_ha.trajectories import Trajectories

def preprocess_trajectories(list_of_trajectories : list[Trajectories]) -> tuple[ list[NDArray[np.float64]],
                                                                                 list[NDArray[np.float64]],
                                                                                 list[tuple[int, int]] ]:
    """
    Converts list of trajectories into a single trajectory.
    We do this conversion in order to avoid discarding 2M data-points from each trajectory during our segmentation
    process (see function diff_method_backandfor() in module compute_derivatives.py).

    :param
        list_of_trajectories: Each element of the list is a trajectory. A trajectory is a 2-tuple of (time, vector),

        where

        time: is a list having a single item. The item is the sampling time, stored as a numpy.ndarray having structure as
           (rows, ) where rows is the number of sample points. The dimension cols is empty meaning a single dim array.
        vector: is a list having a single item. The item is a numpy.ndarray with (rows,cols), rows indicates the number of
           points and cols as the system's dimension. The dimension is the total number of variables in the trajectories
           including both input and output variables.

    :return:
        The lists t_list and y_list containing time and vector as (t_list, y_list) pair and positions.
        Where
        t_list: a single-item list whose item is a numpy.ndarray containing time-values as a concatenated list.
        y_list: a single-item list whose item is a numpy.ndarray containing vector of values (of input and output) as a
            concatenated list of trajectories.
    """

    t_list : list[NDArray[np.float64]] = []
    y_list : list[NDArray[np.float64]] = []
    position = []

    if len(list_of_trajectories) == 1:  # when list_of_trajectories is a single trajectory
        t_list, y_list = list_of_trajectories[0]
        # print("len of t_list =", len(t_list))
        # print("len of t_list[0] =", len(t_list[0]))
        posi=(0, len(t_list[0]))
        position.append(posi)
    else:
        t_list, y_list, position = convert_trajectories_to_single_list(list_of_trajectories)

    return t_list, y_list, position


def convert_trajectories_to_single_list(list_of_trajectories : list[Trajectories]) -> tuple[ list[NDArray[np.float64]],
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
    '''

    t_list = []
    y_list = []
    position = []
    start_posi = 0

    #  ****************************************
    # Create np.array for the first time with the correct dimensions
    trajectory = list_of_trajectories[0]
    t_list_per_traj, y_list_per_traj = trajectory
    temp_t_array_all = t_list_per_traj[0]    # get the time array
    temp_y_array_all = y_list_per_traj[0]  # get the vector array
    total_trajectories = 1
    #  ****************************************

    for traj in list_of_trajectories:
        t_list_per_traj, y_list_per_traj = traj # each traj is a two-tuple containing a list of single item and
                                                # the item is np.array data type
        temp_t_array = t_list_per_traj[0]    # get the time array
        temp_y_array = y_list_per_traj[0]  # get the vector array

        if total_trajectories != 1: # for ==1 we have done outside
            temp_t_array_all = np.concatenate([temp_t_array_all, temp_t_array]) # appending the array in to single dim
            temp_y_array_all = np.vstack([temp_y_array_all, temp_y_array]) # appending the array

        # Computing position needed throughout the algorithm
        data_size = len(t_list_per_traj[0])
        end_posi = start_posi + data_size - 1 # minus 1 because of zero-based indexing
        posi=(start_posi, end_posi)

        start_posi = end_posi + 1 # +1 to start the next indexing sequence
        position.append(posi)
        total_trajectories = total_trajectories + 1

    t_list.append(temp_t_array_all) # converting the array back to list containing a single item
    y_list.append(temp_y_array_all)

    # '''
    # print("t_list is ", t_list)
    # print("shape of t_list=", t_list[0].shape)
    # print("type of t_list=", type(t_list[0]))
    # print("y_list is ", y_list)
    # print("shape of y_list=", y_list[0].shape)
    # print("type of y_list=", type(y_list[0]))
    # print("position = ", position)
    # '''

    return t_list, y_list, position

def parse_trajectories(input_filename : str) -> tuple [ list[tuple[ list[NDArray[np.float64]], list[NDArray[np.float64]] ]],
                                                        float,
                                                        int ]:
    """
    This is a special case function, because the argument input_filename is a filename which contains all
    trajectories concatenated into a single file.
    This function parse this single file containing concatenated trajectories. Note that there is no symbols or special
    marker to separate trajectories. Each trajectory data are appended one below the other. The only indication is the
    value of the first column (contains the simpling time value). For a new trajectory this column value is always 0.0
    i.e. the start time of a new trajectory/simulation.

    :param input_filename: is the input file name containing trajectories.

    :return:
        list_of_trajectories: Each element of the list is a trajectory. A trajectory is a 2-tuple of (time, vector), where
            time: is a list having a single item. The item is the sampling time, stored as a numpy.ndarray having structure
                as (rows, ) where rows is the number of sample points. The dimension cols is empty meaning a single dim array.
            vector: is a list having a single item. The item is a numpy.ndarray with (rows,cols), rows indicates the number of
                points and cols as the system's dimension. The dimension is the total number of variables in the trajectories
                including both input and output variables.
        stepsize: is the sampling time period between two points.
        system_dimension: is the dimension (input + output variables) of the system whose trajectory is being parsed.

    """


    t_list : list[NDArray[np.float64]] = []
    y_list : list[NDArray[np.float64]] = []
    list_of_trajectories : list[tuple[ list[NDArray[np.float64]], list[NDArray[np.float64]] ]] = []
    y_list_per_trajectory : list[list[float]] = []
    y_array_per_trajectory : NDArray[np.float64] # will be converted to numpy.array
    t_list_per_trajectory : list[float] = []
    t_array_per_trajectory : NDArray[np.float64] # will be converted to numpy.array

    seqCount = 0
    with open(input_filename, 'r') as file:
        for line in file:
            colum = 1
            cc = 0
            all_y_pts = []
            # print("test line =", line)
            for word in line.split():
                if colum == 1:
                    if float(word) == 0.0:  # this check will be enabled only on new trajectory series
                        if seqCount != 0:  # meaning we found the next t=0 and not the starting t=0
                            y_array_per_trajectory = np.array(y_list_per_trajectory) # convert list to array in time complexity O(n)
                            y_list.append(y_array_per_trajectory) # store the vector array into a list

                            t_array_per_trajectory = np.array(t_list_per_trajectory) # convert list to array in time complexity O(n)
                            t_list.append(t_array_per_trajectory) # store the array of time values into a list

                            trajectory = (t_list, y_list)   # create a tuple of (time and vector)
                            list_of_trajectories.append(trajectory) # create a list of trajectories

                            #  reset or re-initialize variables for next iterations
                            y_list = []
                            t_list = []
                            y_list_per_trajectory = []
                            t_list_per_trajectory = []

                    t_list_per_trajectory.append(float(word))
                    colum += 1
                else:
                    all_y_pts.append(float(word))
                    cc += 1

            y_list_per_trajectory.append(all_y_pts)
            seqCount += 1

    # Note: the last trajectory to be added now
    y_array_per_trajectory = np.array(y_list_per_trajectory)  # convert list to array in time complexity O(n)
    y_list.append(y_array_per_trajectory)  # store the vector array into a list

    t_array_per_trajectory = np.array(t_list_per_trajectory)  # convert list to array in time complexity O(n)
    t_list.append(t_array_per_trajectory)  # store the array of time values into a list

    trajectory = (t_list, y_list)  # create a tuple of (time and vector of list of single item, where item is np.array)
    list_of_trajectories.append(trajectory)  # create a list of trajectories

#     '''
#     print("y_list = ", y_list)
#     print("totalPoints = ", totalPoints)
#     print("totalPoints in y_list = ", len(y_list))
# 
#     print ("Type of t_list = ", type(t_list))
#     print("Type of type(t_list[0]) = ", type(t_list[0]))
#     print("Type of t_list[0].shape= ", t_list[0].shape)
#     print("Type of t_list[0].shape[0]= ", t_list[0].shape[0])
#     # print("Type of t_list[0].shape[1]= ", t_list[0].shape[1]) Error coz only one dimension available and no cols
#     print ("t_list = ", t_list)
# 
#     print("Type of y_list = ", type(y_list))
#     print("Type of type(y_list[0]) = ", type(y_list[0]))
#     print("Type of y_list[0].shape= ", y_list[0].shape)   # prints the shape of y_list (15015, 5) = (rows, colmns)
#     print("Type of y_list[0].shape[1]= ", y_list[0].shape[1])   # shape[0] for rows or records and shape[1] is cols or dimension
#     # print("y_list = ", y_list)
#     '''
    # print("t_list = ", t_list)
    # print ("t_list[0][2] = ", t_list[0][2])
    # print ("t_list[0][1] = ", t_list[0][1])
    stepsize = t_list[0][2] - t_list[0][1]  # = 0.1 Computing the step-size from the sampled trajectories
    # print("\nComputed Step-size = ", stepsize)

    system_dimension = y_list[0].shape[1]

    return list_of_trajectories, stepsize, system_dimension
