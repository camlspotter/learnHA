"""
This is the main module for inferring an HA model.
"""

import sys  # This is used for command line arguments
from typeguard import typechecked

from infer_ha.segmentation.segmentation import two_fold_segmentation, segmented_trajectories, Segment
from infer_ha.clustering.clustering import select_clustering
from infer_ha.infer_invariants.invariants import compute_mode_invariant
from infer_ha.segmentation.compute_derivatives import diff_method_backandfor
from infer_ha.infer_transitions.compute_transitions import compute_transitions
from infer_ha.clustering.utils import create_simple_modes_positions
from infer_ha.utils.trajectories_parser import preprocess_trajectories
from infer_ha.trajectories import Trajectory, Trajectories
from infer_ha.utils.commandline_parser import Options
from infer_ha.HA import Raw

sys.setrecursionlimit(1000000)  # this is the limit

def infer_model(list_of_trajectories : Trajectories, opts : Options) -> Raw:
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
                                To find the details of the arguments see the file/module "utils/commandline_parser.py"

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
    size_of_input_variables = len(opts.input_variables)
    annotations =  opts.annotations # processed and stored in data-struct
    isInvariant = opts.is_invariant
    clustering_method = opts.clustering_method
    stepM = opts.lmm_step_size # 2 for engine-timing  #  the step size of Linear Multi-step Method (step M)

    t_list, y_list, positions = preprocess_trajectories(list_of_trajectories.trajectories)

    # Apply Linear Multistep Method
    # compute forward and backward version of BDF
    A, b1, b2, Y, ytuple = diff_method_backandfor(y_list, maxorder, list_of_trajectories.stepsize, stepM)

    # ********* Debugging ***********************
    # output_derivatives(b1, b2, Y, size_of_input_variables)
    # ********* Debugging ***********************

    # print("ytuple is = ", ytuple)
    # print("A length=", A.shape)
    # Segment and fit
    # res, drop, clfs = segment_and_fit(A, b1, b2, ytuple,ep) #Amit: uses the simple relative-difference between forward and backward BDF presented in the paper, Algorithm-1.
    # res, drop, clfs, res_modified = segment_and_fit_Modified_two(A, b1, b2, ytuple,ep)
    # res, drop, clfs, res_modified = two_fold_segmentation_new(A, b1, b2, ytuple, size_of_input_variables, method, ep)
    segmented_traj, clfs, drop = two_fold_segmentation(A, b1, b2, ytuple, Y, size_of_input_variables, clustering_method, stepM, ep, ep_backward)
    print("Number of segments =", len(segmented_traj))

    L_y = len(y_list[0][0])  # Number of dimensions
    assert L_y == len(opts.input_variables) + len(opts.output_variables)

    # analyse_variable_index = 2  # zero-based indexing. 0 for refrigeration-cycle. and 2 for engine-timing-system. 3 for AFC
    # analyse_output(segmented_traj, b1, b2, Y, t_list, L_y, size_of_input_variables, stepM, analyse_variable_index)

    # ********* Plotting/Visualizing various points for debugging *************************
    # plot_segmentation_new(segmented_traj, L_y, t_list, Y, stepM) # Trying to verify the segmentation for each segmented points
    # print_segmented_trajectories(segmented_traj)
    # print("positions = ", positions)

    # print("Y = ", Y)
    # print("len of drop = ", len(drop))
    # print("segmented_traj = ", segmented_traj)
    # print("clfs size = ", len(clfs))

    # Instead of deleting the last segment for all models. It is better to ask user's options for deleting
    filter_last_segment = opts.filter_last_segment  # True for delete last segment and False NOT to delete
    # print("filter_last_segment", filter_last_segment)
    segmentedTrajectories, segmented_traj, clfs = segmented_trajectories(clfs, segmented_traj, positions, clustering_method, filter_last_segment) # deleted the last segment in each trajectory
    # print("Segmentation done!")
    # print("segmentedTrajectories = ", segmentedTrajectories)
    # plot_data_values(segmentedTrajectories, Y, L_y)
    # print()
    # ********* Plotting/Visualizing various points for debugging *************************
    # plot_guard_points(segmentedTrajectories, L_y, t_list, Y, stepM) # pre-end and end points of each segment
    # plotdebug.plot_reset_points(segmentedTrajectories_modified, L_y, t_list, Y, stepM) # plotting Reset or Start points
    # plotdebug.plot_segmentation(res, L_y, t_list, Y, stepM) # Trying to verify the segmentation for each segmented points

    # plot_segmentation_new(segmented_traj, L_y, t_list, Y, stepM) # Trying to verify the segmentation for each segmented points

    number_of_segments_before_cluster = len(segmented_traj)
    P_modes, G = select_clustering(segmented_traj, A, b1, clfs, Y, t_list, L_y, opts, stepM) # when len(res) < 2 compute P and G for the single mode
    # print("Fixing Dropped points ...") # I dont need to fix
    # P, Drop = dropclass(P, G, drop, A, b1, Y, ep, stepsize)  # appends the dropped point to a cluster that fits well
    # print("Total dropped points (after fixing) are: ", len(Drop))
    number_of_segments_after_cluster = len(P_modes)
    [init_location] = get_initial_location(P_modes)

    # *************** Trying to plot points ***********************************
    # plotdebug.plot_dropped_points(t_list, L_y, Y, Drop)
    # plot_after_clustering(t_list, L_y, P_modes, Y, stepM)

    mode_inv = compute_mode_invariant(L_y, P_modes, Y, isInvariant)

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

    transitions = compute_transitions(opts.output_directory,
                                      P_modes, positions, segmentedTrajectories, L_y, boundary_order, Y,
                                      annotations,
                                      number_of_segments_before_cluster,
                                      number_of_segments_after_cluster)

    print("input_variables:", opts.input_variables)
    print("output_variables:", opts.output_variables)

    raw = Raw(num_mode= number_of_segments_after_cluster,
              G= G,
              mode_inv= mode_inv,
              transitions= transitions,
              initial_location= init_location,
              ode_degree= opts.ode_degree,
              guard_degree= opts.guard_degree,
              input_variables= opts.input_variables,
              output_variables= opts.output_variables
              )

    return typecheck_ha(raw)

@typechecked
def typecheck_ha( raw : Raw ) -> Raw:
    return raw

def get_initial_location(P_modes : list[list[Segment]]) -> list[int]:
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
    P = create_simple_modes_positions(P_modes)

    minkey = min(enumerate(P), key= lambda x: x[1][0])[0]

    # ToDo: to find all initial location/mode, use the structure segmented_traj: 1st position of each trajectory
    return [minkey]
