import numpy as np
from numpy.typing import NDArray
from typing import cast, Any
from infer_ha.segmentation.segmentation import Segment
from infer_ha.types import MATRIX

def get_signal_data(segmented_traj : list[Segment],
                    Y : MATRIX,
                    b1 : MATRIX,
                    L_y : int,
                    t : MATRIX,
                    size_of_input_variables : int,
                    stepM : int) -> tuple[list[list[list[float]]], list[list[float]]]:
    """
    This is a pre-processing function to obtain the actual signal points of the segmented trajectories.

    :param segmented_traj: is a list of a custom data structure consisting of segmented trajectories (positions). Each item
        of the list contains a tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
        The Tuple has 3 items:
            (1) first a list of two values for recording start and end points for learning ODE
            (2) second a list of two values for recording start and end points for learning guard and assignment using the
            exact point of jump
            (3) third the list of values represent the positions of points of the trajectories.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param t: a numpy.ndarray containing time-values as a concatenated list.
    :param size_of_input_variables: total number of input variables in the given trajectories.
    :return: The segmented signal's actual data points (f_ode) and the corresponding time values (t_ode).
            The time values t_ode is only used for debugging purposes, mainly for plotting.
            Note that the signal returned is projected only on the output variables.
    """

    f_ode = []
    t_ode = []
    # print("len of res=", len(res))
    for seg_element in segmented_traj:

        time_data = []
        # print("leg(segData) is ", len(segData))
        signalData = []
        # ToDo: instead of taking the exact points, for better ODE comparison use segment excluding boundary-points
        for pos_id in seg_element.positions():
            signalData.append([Y[pos_id, dim] for dim in range(size_of_input_variables, L_y)])  # ignore input-variables. * Y contain the actual data-points
            # signalData.append([b1[pos_id, dim] for dim in range(size_of_input_variables, L_y)])  # ignore input-variables. * b1 contain the backward derivatives

            time_data.append(t[pos_id + stepM])  # since Y values are after leaving 5 point from start and -5 at the end
        f_ode.append(signalData)
        t_ode.append(time_data)  # computing time only for plotting reason

    return f_ode, t_ode


def check_correlation_compatible(M1 : MATRIX, M2 : MATRIX) -> tuple[MATRIX, MATRIX]:
    """
    Checks if the numpy array M1 and M2 are compatible for the computation of np.corrcoef() function. There can be cases
    when no variance, for any variable, in the data (rows of M1 or M2 in our case) exits. In such a case calling the
    function np.corrcoef() will return 'nan.' Thus, this function first checks if the standard deviation of a
    variable == 0; we ignore this variable in computing correlation, indicating that the correlation value is one (1)
    as they are correlated. Otherwise, we include the variable for corrcoef computation.

    :param M1: contains the values of the points of the first segmented trajectories.
    :param M2: contains the values of the points of the second segmented trajectories.
    :return: the modified values of M1 and M2 that is compatible for computing np.corrcoef() function.
    """

    # XXX Here, variables go between list and ndarray freely and very hard to make it typed.

    dim = len(M1[1])    # any row will have the same dimension # XXX why not 0?
    # print("dim =", dim)
    newData : list | MATRIX = []
    data : list | MATRIX = []
    for i in range(0, dim):
        d1 : Any = M1[:, i]  # XXX not sure
        standard_deviation = round(np.std(d1), 10)  # rounding for very small standard deviation value
        # XXX This code is fishy...
        if standard_deviation != 0:
            data = np.vstack(d1)
        if len(newData) == 0:
            newData = data
        elif standard_deviation != 0:
            newData = np.column_stack((newData, data))
            
    M1 = cast(MATRIX, newData)

    newData = []
    data = []
    for i in range(0, dim):
        d1 = M2[:, i]  # XXX not sure
        standard_deviation = round(np.std(d1), 10)
        # XXX This code is fishy...
        if standard_deviation != 0:
            data = np.vstack(d1)
        if len(newData) == 0:
            newData = data
        elif standard_deviation != 0:
            newData = np.column_stack((newData, data))

    M2 = cast(MATRIX, newData)

    return M1, M2


def compute_correlation(path : list[float], signal1 : list[list[float]], signal2 : list[list[float]]) -> int:
    """
    This function computes the minimum correlation values of all the variables in the two input signals. The data values
    for computing the correlation are obtained from the two signals (signal1 and signal2). The path gives the
    corresponding data points to be used for computation. The path contains a list of two tuple values of coordinates.
    The first coordinate is the positions of the points in signal1, and the second coordinate gives the points'
    positions in signal2.

    :param path: is the optimal path returned by the library fastdtw() on the two segmented trajectories (signal1 and
                signal2).
    :param signal1: contains the values of the points of the first segmented trajectories.
    :param signal2: contains the values of the points of the second segmented trajectories.
    :return: the minimum correlation values of all the variables in the signals.
    """

    path1 = np.array(path)
    # print("type=", type(path1))
    # print("len of path=", len(path), "    len of path1=", len(path1))
    M1_ = []
    for id in path1[:, 0]:
        M1_.append(signal1[id])
    M2_ = []
    for id in path1[:, 1]:
        M2_.append(signal2[id])
    M1 : MATRIX = np.array(M1_)
    M2 : MATRIX = np.array(M2_)

    M1, M2 = check_correlation_compatible(M1, M2)

    # print("After check M1 = ", M1)
    # print("After check M2 = ", M2)
    if (len(M1)==0):
        return 1

    # ******** We use numpy correlation coefficient function ******
    corel_value = np.corrcoef(M1, M2, rowvar=False) # rowvar=False will consider column as variables and
                                                    # rows as observations for those variables. See document
    # print("corel_value=", corel_value)
    offset_M1 = M1.shape[1]  # shape[1] gives the dimension of the signal
    offset_M2 = M2.shape[1]
    offset = min(offset_M1, offset_M2) #in case M1 and M2 are reduced separately in dimensions due to compatible check
    # print("dim1=",offset_M1, "  dim2=",offset_M2, "  offset=", offset)
    correl_per_variable_wise = np.diagonal(corel_value, offset)
    # print("correl_per_variable_wise=", correl_per_variable_wise)
    correlation_value = min(correl_per_variable_wise)
    # print("min correlation value =", correlation_value)

    return correlation_value


def create_simple_modes_positions(P_modes : list[list[Segment]]) -> list[list[int]]:
    """
      This function transforms/creates a simple data structure from P_modes. The structure is a list of modes.
      Each mode in the list holding only the position values of data points as a single concatenated list. Unlike the
      input argument P_modes is a structure with list of modes and each mode has one or more segments in the mode-list.

      :param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
          Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
          of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
      :return:
          P: holds a list of modes. Each mode is a list of positions. Note here we return all the positions using the
          exact list (including both start_exact and end_exact).
      """

    P = [ [ pos
            for seg in mode
            for pos in seg.positions() ]
          for mode in P_modes ]

    return P


def create_simple_modes_positions_for_ODE(P_modes : list[list[Segment]]) -> list[list[int]]:
    """
      This function transforms/creates a "simple data" structure from P_modes. This simple structure is a list of modes.
      Each mode in the list holding only the position values of data points as a single concatenated list. Unlike the
      input argument P_modes is a structure with list of modes and each mode has one or more segments in the mode-list.

      :param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
          Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
          of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
      :return:
          P: holds a list of modes. Each mode is a list of positions.
          Note here we return all the positions of points that lies inside the boundary (excluding the exact points).
      """

    P = []
    for mode in P_modes:
        data_pos = []
        for segs in mode:
            # make a simple mode
            start_ode = segs.ode[0]
            end_ode = segs.ode[1]
            inexact_seg = list(range(start_ode, end_ode))   # making the list instead of filtering [p1, ..., p_n]
            data_pos.extend(inexact_seg)    # merge/extend only the inexact positions of the segment
        P.append(data_pos)

    return P

def create_simple_modes_positions_for_ODE_with_pruned_segments(P_modes : list[list[Segment]],
                                                               maximum_ode_prune_factor : float) -> list[list[int]]:
    """
     This function transforms/creates a "simple data" structure from P_modes. This simple structure is a list of modes.
     Each mode in the list holding only the position values of data points as a single concatenated list. Unlike the
     input argument P_modes is a structure with list of modes and each mode has one or more segments in the mode-list.
     In addition, in each mode we now only consider total number of segments decided by value maximum_ode_prune_factor.

     :param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
         Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
         of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
     :return:
         P: holds a list of modes. Each mode is a list of positions.
         Note here we return all the positions of points that lies inside the boundary (excluding the exact points). The
         total number of segments in each mode is equal to maximum_ode_prune_factor.
    """

    P = []
    for mode in P_modes:
        data_pos = []
        performance_prune_count = 0
        for segs in mode:
            # make a simple mode
            start_ode = segs.ode[0]
            end_ode = segs.ode[1]
            # xxx Jun: Not +1 for end_ode?  The original code is like this.
            inexact_seg = list(range(start_ode, end_ode))  # making the list instead of filtering [p1, ..., p_n]
            data_pos.extend(inexact_seg)  # merge/extend only the inexact positions of the segment
            performance_prune_count += 1
            if performance_prune_count >= maximum_ode_prune_factor:  # Just this line helps in pruning same segments for performance of ODE computaion
                print("performance_prune_count=", performance_prune_count)
                break       # break the inner for-loop.
        P.append(data_pos)

    return P


def create_simple_per_segmented_positions(segmented_traj : list[Segment]) -> list[list[int]] :
    """
    This function transforms/creates a simple list structure from segmented_traj. This simple list consists of positions.
    Each item of the list holds only the position values of data points after segmentation.

    :param segmented_traj: is a list of a custom data structure consisting of segmented trajectories (positions). Each item
    of the list contains a tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
    The Tuple has 3 items:
        (1) first a list of two values for recording start and end points for learning ODE
        (2) second a list of two values for recording start and end points for learning guard and assignment using the
        exact point of jump
        (3) third the list of values represent the positions of points of the trajectories.
    :return:
      res: a simple list of positions of the segmented trajectories. Segmented positions is a list containing
      positions of points in the trajectories.
      Note here we return all the positions of points that lies inside the boundary (excluding the exact points).
      This is particularly suitable for ODE inference.
    """

    res = []
    for segs in segmented_traj:
        # segs a tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
        start_ode = segs.ode[0]
        end_ode = segs.ode[1]
        inexact_seg = list(range(start_ode, end_ode + 1))   # making the list instead of searching/filtering from [p1, ..., p_n]
        res.append(inexact_seg)

    return res

def create_simple_per_segmented_positions_exact(segmented_traj : list[Segment]) -> list[list[int]]:
    """
    This function transforms/creates a simple list structure from segmented_traj. This simple list consists of positions.
    Each item of the list holds only the position values of data points after segmentation.

    :param segmented_traj: is a list of a custom data structure consisting of segmented trajectories (positions). Each item
    of the list contains a tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
    The Tuple has 3 items:
        (1) first a list of two values for recording start and end points for learning ODE
        (2) second a list of two values for recording start and end points for learning guard and assignment using the
        exact point of jump
        (3) third the list of values represent the positions of points of the trajectories.
    :return:
      res: a simple list of positions of the segmented trajectories. Segmented positions is a list containing
      positions of points in the trajectories.
      Note here we return all the positions of points of a segment (including the exact points or boundary points).

    """

    return [ list(seg.positions()) for seg in segmented_traj ]
