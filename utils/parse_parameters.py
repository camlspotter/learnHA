"""
This module is takes a filename as input and parse the file line-by-line and word-by-word to create a data structure of
as a list of trajectories to be passsed as input to the learning algorithm.
"""

import numpy as np

def parse_trajectories(input_filename):
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


    t_list = []
    y_list = []
    t_tmp = []
    y_tmp = []
    list_of_trajectories = []
    y_list_per_trajectory = []
    y_array_per_trajectory = [] # will be converted to numpy.array
    t_list_per_trajectory = []
    t_array_per_trajectory = [] # will be converted to numpy.array

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


