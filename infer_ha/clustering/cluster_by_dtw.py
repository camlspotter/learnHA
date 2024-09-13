"""
This module contains our approach to clustering using the DTW algorithm.

"""

from typing import Any
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw         # https://pypi.org/project/fastdtw/
from sklearn import linear_model
from infer_ha.clustering.utils import get_signal_data, compute_correlation, \
    create_simple_modes_positions_for_ODE_with_pruned_segments
from infer_ha.utils.util_functions import matrowex
import numpy as np
from numpy.typing import NDArray
# from infer_ha.clustering.utils import create_simple_modes_positions_for_ODE
# from ..helpers.plotDebug import print_segmented_trajectories, print_P_modes
# from ..helpers import plotDebug as plotdebug
from infer_ha.segmentation.segmentation import Segment
from infer_ha.types import MATRIX, Span

def get_desired_ODE_coefficients(P_modes : list[list[Segment]],
                                 A : MATRIX,
                                 b1 : MATRIX,
                                 maximum_ode_prune_factor : int) -> list[MATRIX]:
    r"""
    ODE inference.
    This function computes the coefficients of the polynomial ODE for each cluster/mode. Note during ODE coefficient
    inferring we only consider in each mode the total number segements <= maximum_ode_prune_factor which is a value
    supplied by the user as arguments for pruning redundant segments.

    :param P_modes: hols a list of modes. Each mode is a list of structures; we call it a segment.
        Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
    :param A: For every point of a trajectory the coefficients of the monomial terms obtained using the \Phi
         function (or the mapping function) as mention in Jin et al. paper.
    :param b1: the derivatives of each point computed using the backward version of BDF.
    :param maximum_ode_prune_factor: integer value supplied by the user to decide the prune factor for ODE inference.
    :return: The computed cluster and the coefficients of the polynomial ODE.
        # P: holds a list of modes. Each mode is a list of structures; we call it a segment.
        # Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        # of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
        G: is a list containing the list of the coefficients of the polynomial ODE.

    """
    # Debug ----------------
    # print_P_modes(P_modes)
    # ----------------


    # P = create_simple_modes_positions_for_ODE(P_modes)  # for ODE inference we use segment excluding boundary points
    # for ODE inference we use segments
    P : list[list[Span]] = create_simple_modes_positions_for_ODE_with_pruned_segments(P_modes, maximum_ode_prune_factor)
        # excluding boundary points. The number of segments in each mode is decided by the prune factor for performance.

    # print("Sort clusters based on Data-size and take the first num_mode clusters")
    length_and_modepts = [(len(p_i), p_i) for p_i in P]  # create a list of 2-tuple
    # length_and_modepts.sort(reverse=True)  # this data is sorted from highest number of points in the cluster to lowest
    # print("DTW: Total clusters = ", len(length_and_modepts))

    #  ***************************************************************
    num_mode = len(length_and_modepts) # Made this change after Paper submission (in the paper engineTiming which was 42
    # reduced to 20 although this will not have effect, since only the first 4 modes were used to generate trajectories
    # now we removed from the argument passing num_mode as user decided argument
    #  ***************************************************************

    mode_pts = [ mode_ptsi for (_datasize, mode_ptsi) in length_and_modepts ]

    # Fit each cluster again
    def fit(spans : list[Span]) -> Any:  # = LinearRegression
        pt = [ x for span in spans for x in span.range() ]
        clf = linear_model.LinearRegression(fit_intercept=False)
        clf.fit(matrowex(A, pt), matrowex(b1, pt))
        return clf

    clfs = [ fit(pt) for pt in mode_pts ]

    # P = mode_pts    # we do not want to return simple-segmented-modes
    G : list[MATRIX] = [clf.coef_ for clf in clfs]

    return G

def cluster_by_dtw(segmented_traj : list[Segment],
                   A : MATRIX,
                   b1 : MATRIX,
                   Y : MATRIX,
                   t : MATRIX,
                   L_y : int,
                   correl_threshold : float,
                   distance_threshold : float,
                   size_of_input_variables : int,
                   stepM : int,
                   maximum_ode_prune_factor : int=50) -> tuple[list[list[Segment]], list[MATRIX]]:
    r"""
    This function contains our approach to clustering using the DTW algorithm.

    :param segmented_traj: is a list of a custom data structure consisting of segmented trajectories (positions). Each
        item of the list contains tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
        The Tuple has three items:
            (1) first, a list of two values for recording start and end points for learning ODE
            (2) second, a list of two values for recording start and end points for learning guard and assignment using
            the exact point of a jump
            (3) third, a list of values representing the position of points of the trajectories.
    :param A: For every point of a trajectory the coefficients of the monomial terms obtained using the \Phi
         function (or the mapping function) as mention in Jin et al. paper.
    :param b1: the derivatives of each point computed using the backward version of BDF.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :param t: a numpy.ndarray containing time-values as a concatenated list.
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param correl_threshold: threshold value for correlation for DTW comparison of two segmented trajectories.
    :param distance_threshold: threshold value for distance for DTW comparison of two segmented trajectories.
    :param size_of_input_variables: total number of input variables in the given trajectories.
    :param maximum_ode_prune_factor: maximum number of segments to be used for ODE computation per cluster/mode.
    :return: The computed cluster and the coefficients of the polynomial ODE.
        P: holds a list of modes. Each mode is a list of structures; we call it a segment.
        Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
        G: is a list containing the list of the coefficients of the polynomial ODE.
    """

    # holds a list of modes and each mode is a list of segments and a mode is a list of segment
    P : list[list[Segment]] = []
            # Thus P = [mode-1, mode-2, ... , mode-n]
            # and mode-1 = [ segment-1, ... , segment-n]
            # and segment-1 = ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n])
    # *******************************************************************************************
    # get the segmented signal from trajectory.
    ft : tuple[ list[list[list[float]]],
                list[list[float]] ] = get_signal_data(segmented_traj, Y, b1, L_y, t,
                                                      size_of_input_variables, stepM)
    (f_ode, t_ode) = ft

    # print("f_ode is ", f_ode)
    # *******************************************************************************************

    # ******** To estimate the maximum and minimum values during clustering DTW ********
    min_distance = 1e10
    max_distance = 0
    min_correl = 1
    max_correl = -1
    # *********************************************************************************

    # ******************************************************************
    # to keep the OLD implementation's variable
    res = segmented_traj  

    # ******************************************************************
    count = len(res)

    # P.append(res[0]) # stores the first segment
    #  ********* Debugging ***********
    # file_csv = open('clusterProcessFile.csv','w')
    # writer = csv.writer(file_csv)   # file pointer created
    # rowValue = ["i", "j", "Seg_i-time-start", "time-end", "Seg_j-time-start", "time-end", "distance", "correlation", "Cluster-ID"]
    # writer.writerow(rowValue)
    # ***************************************
    f_ode1 = f_ode
    t_ode1 = t_ode  # t_ode is used only for plotting for debugging
    # makes a copy of the segmented_traj for working
    res1 = res
    res2 = res1
    i = 0    # j = 0
    myClusterCount = 0
    while i < count:
        j = i + 1
        mode = [res1[i]]  # to hold list of segments per mode; initialize the first segmented_traj
        delete_position = []
        while j < count:  #  runs once for each f_ode_[i]
            # print("i=", i, " :f_ode[i] is ", f_ode[i])
            # print(" and j=", j, "  :f_ode[j] is ", f_ode[j])
            dataSize = len(f_ode[i])
            if len(f_ode[i]) > 5:
                dataSize = 5    # setting a small datasize for performance, tradeoff with accuracy
            # half_dataSize = math.ceil(len(f_ode[i])/2)
            # dataSize = half_dataSize     #len(f_ode[i])
            distance1, path = fastdtw(f_ode[i], f_ode[j], radius=dataSize, dist=euclidean)
            distance = distance1 / (len(f_ode[i]) + len(f_ode[j]))
            correlValue = compute_correlation(path, f_ode[i], f_ode[j])
            min_distance = min(distance, min_distance)
            max_distance = max(distance, max_distance)
            min_correl = min(correlValue, min_correl)
            max_correl = max(correlValue, max_correl)
            # length_seg_i = len(t_ode[i]) - 1
            # length_seg_j = len(t_ode[j]) - 1

            # Debugging ******************
            # rowValue = [i, j, t_ode[i][0], t_ode[i][length_seg_i], t_ode[j][0], t_ode[j][length_seg_j], distance, correlValue, myClusterCount]
            # writer.writerow(rowValue)
            # if (correlValue > correl_threshold):
            # print("i=", i, " and j=", j, " :  distance1 = ", distance1, " :  distance = ", distance, "   and   correlation = ", correlValue)

            # if (i==0 and j>=7 and j<=8):
            # plotdebug.plot_signals(t_ode[i], f_ode[i], t_ode[j], f_ode[j])
            # Debugging ******************

            # This feature can also be used, when distance-threshold is not considered as parameter
            if correlValue >= correl_threshold and distance_threshold == 0:  # distance_threshold is disabled or ignored
                # print("******************************************** Found *******************************")
                # print("i=", i, " and j=", j, " : Ignored distance = ", distance, "   and   correlation = ", correlValue)

                mode.append(res1[j])
                delete_position.append(j)


            if correlValue >= correl_threshold and (distance_threshold > 0 and distance < distance_threshold):  # distance is also compared. distance_threshold is threshold value to be supplied wisely
                # print("i=", i, " and j=", j, " :  distance1 = ", distance1, " :  distance = ", distance
                #       "   and   correlation = ", correlValue)
                # print("******************************************** Found *******************************")
                # print("i=", i, " and j=", j, " :  Distance = ", distance, "   and   correlation = ", correlValue)

                mode.append(res1[j])
                delete_position.append(j)

            j = j + 1

        P.append(mode)  # creating the list of modes, with each mode as a list of segments

        # for all delete_position now delete list and update for next iterations
        for val in reversed(delete_position):
            f_ode1.pop(val)
            t_ode1.pop(val)
            res2.pop(val)
        count = len(f_ode1)   # //update the new length of the segments
        f_ode = f_ode1        # //update the new list of ODE data after clustering above
        t_ode = t_ode1
        res1 = res2
        i = i + 1  # reset for next cluster
        myClusterCount += 1

    # print("CLUSTERING: Distance[min,max] = [", min_distance," , ", max_distance,"]")
    # print("CLUSTERING: Correlation[min,max] = [", min_correl, " , ", max_correl, "]")


    # Pruning using maximum_ode_prune_factor is applied only for ODE inference. However, we will still have all the
    # segments in the P data structure, since for inferring guards and assignments the more segments (and so more data)
    # we have the more accurate guard and assignments can be inferred.
    G = get_desired_ODE_coefficients(P, A, b1, maximum_ode_prune_factor)

    return P, G
