"""
This wrapper module enables the selection of different approaches to the clustering algorithm.
Using this wrapper module, one can implement and test different approaches to the clustering algorithm.
Below we have three approaches:
1) 'piecelinear': the original approach in the paper by Jin et al.
2) 'dbscan': The standard DBSCAN clustering
3) 'dtw': The approach using the DTW algorithm.

The learning algorithm is currently designed by focusing on the DTW algorithm.
"""

import numpy as np
from numpy.typing import NDArray
from hybridlearner.inference.options import ClusteringMethod, Options
from hybridlearner.segmentation import Segment
from .cluster_by_dtw import cluster_by_dtw
from .cluster_by_others import dbscan_cluster, merge_cluster_tol2


def select_clustering(
    segmented_traj: list[Segment],
    A: NDArray[np.float64],
    b1: NDArray[np.float64],
    clfs: list[NDArray[np.float64]],
    Y: NDArray[np.float64],
    t: NDArray[np.float64],
    L_y: int,
    input_variables: list[str],
    opts: Options,
    stepM: int,
) -> tuple[list[list[Segment]], list[NDArray[np.float64]]]:
    r"""
    A wrapper module that enables the selection of different approaches to the clustering algorithm.

    :param segmented_traj: is a list of a custom data structure consisting of segmented trajectories (positions). Each item
        of the list contains a tuple of the form ([start_ode, end_ode], [start_exact, end_exact], [p_1, ... , p_n]).
        The Tuple has 3 items:
            (1) first a list of two values for recording start and end points for learning ODE
            (2) second a list of two values for recording start and end points for learning guard and assignment using the
            exact point of jump
            (3) third the list of values represent the positions of points of the trajectories.
    :param A: For every point of a trajectory the coefficients of the monomial terms obtained using the \Phi
         function (or the mapping function) as mention in Jin et al. paper.
    :param b1: the derivatives of each point computed using the backward version of BDF.
    :param clfs: is a list. Each item of the list clfs is a list that holds the coefficients (obtained using linear
        regression) of the ODE of each segment of the segmented trajectories.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :param t: a numpy.ndarray containing time-values as a concatenated list.
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param opts: is a dictionary data structure having the list of commandline arguments passed by the
        user for the learning algorithm.
    :return: The computed cluster and the coefficients of the polynomial ODE.
        P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
        Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
        G: is a list containing the list of the coefficients of the polynomial ODE.
    """

    # print("Clustering segmented points ...")
    maxorder = opts.ode_degree
    num_mode = opts.modes
    ep = opts.segmentation_error_tol
    size_of_input_variables = len(input_variables)
    method = opts.clustering_method
    maximum_ode_prune_factor = opts.ode_speedup
    correl_threshold = opts.threshold_correlation
    distance_threshold = opts.threshold_distance
    dbscan_eps_dist = opts.dbscan_eps_dist
    dbscan_min_samples = opts.dbscan_min_samples

    P_modes: list[list[Segment]] = []
    G: list[NDArray[np.float64]] = []

    # Choice of Clustering Algorithm
    match method:
        case ClusteringMethod.PIECELINEAR:
            if len(segmented_traj) > num_mode:
                assert False, "We do not support piecelinear clustering algorithm!!"
                # P_modes, G = merge_cluster_tol2(res, A, b1, num_mode, ep)  # This is Algo-2:InferByMerge function in Jin et al.
                # Todo: note this approach does not scale well in clustering high number of segments into low modes.

        case ClusteringMethod.DBSCAN:
            assert False, "We do not support this clustering algorithm anymore. We have now modifed the number of data structure, it requires some modification to support it again!!"
            # exit(1)
            # P_modes, G = dbscan_cluster(clfs, segmented_traj, A, b1, num_mode, dbscan_eps_dist, dbscan_min_samples, size_of_input_variables)
            # print("Total Clusters after DBSCAN algorithm = ", len(P_modes))

        case ClusteringMethod.DTW:
            # print("Running clustering using  DTW algorithm!!")
            P_modes, G = cluster_by_dtw(
                segmented_traj,
                A,
                b1,
                Y,
                t,
                L_y,
                correl_threshold,
                distance_threshold,
                size_of_input_variables,
                stepM,
                maximum_ode_prune_factor,
            )
            print("Total Clusters after DTW algorithm = ", len(P_modes))

    return P_modes, G
