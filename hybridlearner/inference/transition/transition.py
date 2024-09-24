"""
This module is used for computing transitions of an HA.

"""

from hybridlearner.inference.transition.annotation import apply_annotation
from hybridlearner.inference.transition.connection import create_connection
from hybridlearner.inference.transition.assignment import compute_assignment
from hybridlearner.inference.transition.guards import getGuard_inequality
from hybridlearner.segmentation import Segment
from hybridlearner.types import MATRIX, Span
from hybridlearner.inference.annotation import AnnotationTbl
from hybridlearner.inference.transition.assignment import Assignment

Transition = tuple[
    int,  # src
    int,  # dest
    # guard coeffs [ci], defines the guard:  x1 * c1 + x2 * c2 + .. + 1 * cn <= 0
    list[float],
    # x'j = x1 * cj1 + x2 * cj2 + .. + xn *cjn + ij
    Assignment,
]


def compute_transitions(
    output_dir: str,
    # segments in clusters
    P_modes: list[list[Segment]],
    # The positions of the full segments in the trajectories
    segmentedTrajectories: list[list[Span]],
    # number of the input and output variables
    L_y: int,
    boundary_order: int,
    Y: MATRIX,
    annotations: AnnotationTbl,
    number_of_segments_before_cluster: int,
    number_of_segments_after_cluster: int,
) -> list[Transition]:
    """
    This function decides to compute or ignore mode-invariant computation based on the user's choice.


    :param output_dir: output directory.
    :param P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
        Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
        of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
    :param position: is a list of position data structure. Each position is a pair (start, end) position of a trajectory.
        For instance, the first item of the list is [0, 100] means that the trajectory has 101 points. The second item
        as [101, 300], meaning the second trajectory has 200 points. Note that all the trajectories are concatenated.
    :param segmentedTrajectories: is a data structure containing the positions of the segmented trajectories that keeps
        track of the connections between them.
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param boundary_order: degree of the polynomial concerning the guard's equation.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :param annotations: specific data structure holding user's information about type annotation values.
    :param number_of_segments_before_cluster: total number of segments obtained using the segmentation process and
        before applying the clustering algorithm.
    :param number_of_segments_after_cluster: total number of segments obtained after applying the clustering algorithm.
    :return: A list of transitions of type [src_mode, dest_mode, guard_coeff, assignment_coeff, assignment_intercept].
        Where src_mode, and dest_mode store the source and destination location ID. The guard_coeff structure holds the
        coefficients of the guard polynomial. Whereas assignment_coeff and assignment_intercept contain the
        coefficients and intercepts value for the assignment equations.

    """
    traj_size = len(segmentedTrajectories)

    # print("Computing Connecting points for Transitions ...")
    connections = create_connection(P_modes, segmentedTrajectories)
    # print("Computing Connecting points done!")
    # print("len(data_points) =",len(data_points))
    # print("data_points=", data_points)

    # If a model is a single-mode system for instance, lets say our segmentation identifies a full trajectory as a
    # single mode. And this is true for all input trajectories (say init-size 10 and all 10 trajectories are learned
    # as a single-mode system), then such model do not have/need to learn Transition.
    # So number_of_segments_after_cluster is 1 but number_of_segments_before_cluster will be 10 (initial init-size)
    # Therefore, we need to handle it carefully
    # Fixing separately for single-mode system like Bouncing Ball or single-mode systems without transition.
    # E.g. in the case of bouncing ball all segments are clustered into One.
    if (
        number_of_segments_after_cluster == 1
        and number_of_segments_before_cluster >= 1
        and traj_size == number_of_segments_before_cluster
    ):
        return []  # transitions here is empty for a single mode system without transition.

    # data_points contains list of connecting points for each Transition
    # Note we are considering possible transition only based on the given trajectory-data.
    # *************** Trying to plot these points. Also creating transition ***********************************
    transitions: list[tuple[int, int, list[float], Assignment]] = []
    for conn in connections:
        links = conn.links
        src_mode = conn.src_mode
        dest_mode = conn.dst_mode

        # Now we only use a few connecting-points [pre_end_point and end_point] to find guard using SVM
        # ******* Step-1: create the source and destination list of positions and Step-2: call getGuardEquation()
        srcData = [link.src_end - 1 for link in links]
        destData = [link.src_end for link in links]

        # C++ code assumes the first element of guard_coeff is either 0, 1 or -1
        guard = normalize_guard(
            getGuard_inequality(output_dir, srcData, destData, L_y, boundary_order, Y)
        )

        '''
        We will not check any complex condition. We simply apply linear regression to first learn the assignments.
        Then, we check the condition for annotations and whenever annotation information is available we replace
         the computed (learned using linear regression) values using our approach of annotations.
        '''
        assignment: Assignment = compute_assignment(links, L_y, Y)
        assignment = apply_annotation(Y, annotations, links, assignment)

        transitions.append((src_mode, dest_mode, guard, assignment))

    return transitions


def normalize_guard(coeffs: list[float]) -> list[float]:
    # first column coefficient, can be used to divide on both sides to normalize. Taking only value not sign
    coeff0_abs = abs(coeffs[0])
    if coeff0_abs != 0:
        coeffs = [c / coeff0_abs for c in coeffs]
    return coeffs
