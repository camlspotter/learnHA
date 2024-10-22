"""
This is the main module for inferring an HA model.
"""

import sys  # This is used for command line arguments
from typeguard import typechecked
import numpy as np
from pydantic.dataclasses import dataclass
from pydantic import ConfigDict

from hybridlearner.segmentation import (
    two_fold_segmentation,
    segmented_trajectories,
    Segment,
)
from hybridlearner.inference.clustering import select_clustering
from hybridlearner.inference.invariant import compute_invariant
from hybridlearner.inference.annotation import convert_annotation_dict, AnnotationTbl
from hybridlearner.segmentation.derivatives import diff_method_backandfor
from hybridlearner.inference.transition import Transition, compute_transitions
from hybridlearner.trajectory import (
    Trajectories,
    preprocess_trajectories,
    trajectory_stepsize,
)
from hybridlearner.inference.options import Options
from hybridlearner.types import MATRIX, Span

sys.setrecursionlimit(1000000)  # this is the limit


# Some magic is required to include np.ndarray in dataclass
@dataclass(config=ConfigDict(arbitrary_types_allowed=True))
class Raw:
    num_mode: int  # num_mode
    # ODE coeffs and intercepts, called Flow in the paper.  The array size is (#vars + 1) * #ovars
    G: list[np.ndarray]
    mode_inv: list[list[tuple[float, float]]]  # Variable invariants per mode
    transitions: list[Transition]
    initial_location: int
    ode_degree: int  # required for printing
    guard_degree: int  # required for printing

    input_variables: list[str]
    output_variables: list[str]


def infer_model(
    list_of_trajectories: Trajectories,
    input_variables: list[str],
    output_variables: list[str],
    opts: Options,
) -> Raw:
    """
    The main module to infer an HA model for the input trajectories.

    :param list_of_trajectories: Each element of the list is a trajectory. A trajectory is a 2-tuple of (time, vector), where
            time: is a list having a single item. The item is the sampling time, stored as a numpy.ndarray having structure
                as (rows, ) where rows is the number of sample points. The dimension cols is empty meaning a single dim array.
            vector: is a list having a single item. The item is a numpy.ndarray with (rows,cols), rows indicates the number of
                points and cols as the system's dimension. The dimension is the total number of variables in the trajectories
                including both input and output variables.
    :param opts: is a dictionary data structure containing all the parameters required for our learning
                                algorithm. The arguments of the opts can also be passed as a command-line
                                arguments. The command-line usages can be obtained using the --help command.
                                To find the details of the arguments see the file/module "inference.options"

    :return:
        P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
        Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
        Each of the values p1,...,p_n are positions of points of a trajectories.
        The size of the list P_modes is equal to the number of clusters or modes of the learned hybrid automaton (HA).
        G: is a list. Each item of the list G is a list that holds the coefficients (obtained using linear regression)
           of the ODE of a mode of the learned HA.
        mode_inv: is a list with items of type [mode-id, invariant-constraints]. Where mode-id is the location number
                  and invariant-constraints holds the bounds (min, max) of each variable in the corresponding mode-id.
        transitions: is a list with structure [src_mode, dest_mode, guard_coeff, assignment_coeff, assignment_intercept]
                     where
            src_mode: is the source location number
            dest_mode: is the destination location number
            guard_coeff: is a list containing the coefficient of the guard equation (polynomial)
            assignment_coeff: is a list containing the coefficient of the assignment equations (from linear regression)
            assignment_intercept: is a list containing the intercepts of the assignment equations (linear regression)
        positions: is a list containing positions of the input list_of_trajectories. This structure is required for printing
            the HA model. Particularly, to get the starting positions of input trajectories for identifying initial mode(s).
    """

    maxorder = opts.ode_degree
    boundary_order = opts.guard_degree
    ep = opts.segmentation_error_tol
    ep_backward = opts.segmentation_fine_error_tol
    size_of_input_variables = len(input_variables)
    isInvariant = opts.is_invariant
    clustering_method = opts.clustering_method
    # the step size of Linear Multi-step Method (step M)
    stepM = opts.lmm_step_size

    annotations: AnnotationTbl = convert_annotation_dict(
        input_variables, output_variables, opts.annotations
    )

    # Concatenate all the trajectories.
    t: MATRIX  # times, 1D
    y: MATRIX  # values, 2D
    # The positions of the original trajectories in the concatenated one
    traj_spans: list[Span]
    t, y, traj_spans = preprocess_trajectories(list_of_trajectories)

    # plot of preprocessed trajectories
    tys = [
        (
            np.array(t[span.start : span.end + 1]),
            np.array(y[span.start : span.end + 1][:]),
        )
        for span in traj_spans
    ]

    # Apply Linear Multistep Method
    # compute forward and backward version of BDF
    A: MATRIX
    b1: MATRIX
    b2: MATRIX
    Y: MATRIX  # slice of y, dropping the first and last stepM samples
    npoints: int
    A, b1, b2, Y, npoints = diff_method_backandfor(
        y, maxorder, trajectory_stepsize(list_of_trajectories[0]), stepM
    )
    # L_y: length (nrows) of y
    L_y = len(input_variables) + len(output_variables)

    # ********* Debugging ***********************
    # output_derivatives(b1, b2, Y, size_of_input_variables)
    # ********* Debugging ***********************

    # print("A length=", A.shape)
    # Segment and fit
    # res, drop, clfs = segment_and_fit(A, b1, b2, npoints, ep) #Amit: uses the simple relative-difference between forward and backward BDF presented in the paper, Algorithm-1.
    # res, drop, clfs, res_modified = segment_and_fit_Modified_two(A, b1, b2, npoints, ep)
    # res, drop, clfs, res_modified = two_fold_segmentation_new(A, b1, b2, npoints, size_of_input_variables, method, ep)

    segments: list[Segment]
    clfs: list[MATRIX]
    drop: list[int]
    segments, clfs, drop = two_fold_segmentation(
        A,
        b1,
        b2,
        npoints,
        Y,
        size_of_input_variables,
        clustering_method,
        stepM,
        ep,
        ep_backward,
    )

    # analyse_variable_index = 2  # zero-based indexing. 0 for refrigeration-cycle. and 2 for engine-timing-system. 3 for AFC
    # analyse_output(segments, b1, b2, Y, t, L_y, size_of_input_variables, stepM, analyse_variable_index)

    # ********* Plotting/Visualizing various points for debugging *************************
    # plot_segmentation_new(segments, L_y, t, Y, stepM) # Trying to verify the segmentation for each segmented points
    # print_segmentsectories(segments)

    # Group the segments by trajectories.
    # The last segment of each trajectory is dropped since it is often truncated.

    # True to delete the last segment and False NOT to delete
    filter_last_segment = opts.filter_last_segment
    segmentedTrajectories: list[list[Span]]
    segmentedTrajectories, segments, clfs = segmented_trajectories(
        clfs, segments, traj_spans, clustering_method, filter_last_segment
    )
    # 1 segmentedTrajectory per trajectory
    assert len(segmentedTrajectories) == len(traj_spans)

    # plot_data_values(segmentedTrajectories, Y, L_y)
    # ********* Plotting/Visualizing various points for debugging *************************
    # plot_guard_points(segmentedTrajectories, L_y, t, Y, stepM) # pre-end and end points of each segment
    # plotdebug.plot_reset_points(segmentedTrajectories_modified, L_y, t, Y, stepM) # plotting Reset or Start points
    # plotdebug.plot_segmentation(res, L_y, t, Y, stepM) # Trying to verify the segmentation for each segmented points
    # plot_segmentation_new(segments, L_y, t, Y, stepM) # Trying to verify the segmentation for each segmented points

    number_of_segments_before_cluster = len(segments)
    print("num of segments before clustering", number_of_segments_before_cluster)
    print("num of segmentedTrajectories", len(segmentedTrajectories))

    P_modes: list[list[Segment]]
    G: list[MATRIX]
    # when len(res) < 2 compute P and G for the single mode
    P_modes, G = select_clustering(
        segments, A, b1, clfs, Y, t, L_y, input_variables, opts, stepM
    )

    # print("Fixing Dropped points ...") # I dont need to fix
    # P, Drop = dropclass(P, G, drop, A, b1, Y, ep, stepsize)  # appends the dropped point to a cluster that fits well
    # print("Total dropped points (after fixing) are: ", len(Drop))
    number_of_segment_clusters = len(P_modes)
    print("num of segment clusters", number_of_segment_clusters)
    # print(P_modes)

    init_location: int
    [init_location] = get_initial_location(P_modes)

    # *************** Trying to plot points ***********************************
    # plotdebug.plot_dropped_points(t, L_y, Y, Drop)
    # plot_after_clustering(t, L_y, P_modes, Y, stepM)

    mode_inv: list[list[tuple[float, float]]]
    mode_inv = (
        compute_invariant(L_y, P_modes, Y) if isInvariant else [[]] * len(P_modes)
    )

    # *************** Trying to plot the clustered points ***********************************
    # print("Number of num_mode= ", num_mode)
    # print("Number of Clusters, len(P)=", len(P))
    # '''
    # TODO: remove taking input 'num_mode' from user
    #
    # if (len(P) < num_mode):
    #     print("Number of desired Modes = ", num_mode)
    #     num_mode = len(P)
    #     print("Number of Clusters Learned = ", len(P))
    # '''
    # num_mode = len(P)

    transitions: list[Transition]
    transitions = compute_transitions(
        opts.output_directory,
        P_modes,
        segmentedTrajectories,
        L_y,
        boundary_order,
        Y,
        annotations,
        number_of_segments_before_cluster,
        number_of_segment_clusters,
    )

    raw = Raw(
        num_mode=number_of_segment_clusters,
        G=G,
        mode_inv=mode_inv,
        transitions=transitions,
        initial_location=init_location,
        ode_degree=opts.ode_degree,
        guard_degree=opts.guard_degree,
        input_variables=input_variables,
        output_variables=output_variables,
    )

    return typecheck_ha(raw)


@typechecked
def typecheck_ha(raw: Raw) -> Raw:
    return raw


def get_initial_location(P_modes: list[list[Segment]]) -> list[int]:
    """
    At the moment we are printing only the mode-ID where the first/starting trajectory is contained in.
    Finding other initial modes, require searching segmented trajectories and identifying the probable initial positions
    of the trajectories. Probable because we still drop points during segmentation (the start-point of a segmented trajectory).
    This dropping of points (in addition to the first M points, where M is the step in LMM) makes it hard to track the
    position of the initial trajectories using the data-structure position.

    @param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
           Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
           of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
           The size of the list P is equal to the number of clusters or modes of the learned hybrid automaton (HA).
    @param position: is a list containing positions for the input list-of-trajectories.
    @return:
        init_locations: contains a list of initial location ID(s), having zero based indexing.

    """
    P: list[list[Span]] = [[seg.exact for seg in mode] for mode in P_modes]

    # x[1] to get P's element
    minkey: int = min(enumerate(P), key=lambda x: x[1][0].start)[0]

    # ToDo: to find all initial location/mode, use the structure segments: 1st position of each trajectory
    return [minkey]
