"""
This module contains functions for computing mode-invariants.
Currently, a simple over-approximation approach is applied to compute the mode-invariant.
We use a straightforward approach to compute each variable's bound values (Min, Max) in each mode.
A more complex approach can be implemented and tested in this module.
"""

import numpy as np
from numpy.typing import NDArray
from operator import itemgetter

from infer_ha.clustering.utils import create_simple_modes_positions
from infer_ha.segmentation.segmentation import Segment

def compute_mode_invariant(L_y : int,
                           P_modes : list[list[Segment]],
                           Y : NDArray[np.float64],
                           invariant_enabled : bool) -> list[list[tuple[float, float]]]:
    """
    This function decides to compute or ignore mode-invariant computation based on the user's choice.

    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param P_modes: hols a list of modes. Each mode is a list of structures; we call it a segment.
          Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
          of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :param invariant_enabled: is the user's choice of computing or ignoring invariant. The value 0 and 1 to compute and
        2 for ignoring.
    :return: A list of values of type [mode-id, invariant-constraints]. mode-id is the location ID and
        invariants-constraints is the list of (min,max) bounds of each variable. The order of the variable is maintained.

    """

    if invariant_enabled:
        mode_inv = compute_invariant(L_y, P_modes, Y)
        print("Computing Mode Invariant done!")
        return mode_inv
    else:
        print("Computing Mode Invariant IGNORED!")
        return []

def compute_invariant (L_y : int,
                       P_modes : list[list[Segment]],
                       Y : NDArray[np.float64]) -> list[list[tuple[float,float]]]:
    """
    This function computes the invariant for each mode/cluster.

    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param  P_modes: holds a list of modes. Each mode is a list of structures; we call it a segment.
          Thus, P = [mode-1, mode-2, ... , mode-n] where mode-1 = [ segment-1, ... , segment-n] and segments are
          of type ([start_ode, end_ode], [start_exact, end_exact], [p1, ..., p_n]).
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :return: A list of values of type [mode-id, invariant-constraints]. mode-id is the location ID and
       invariants-constraints is the list of (min,max) bounds of each variable.
       The order of the variable is maintained in the list.


    """

    P : list[list[int]] = create_simple_modes_positions(P_modes)

    x_pts : list[dict[int, float]] = []

    '''
    Example:
    invariant =[]
    mode_inv = []        
    invariant.append([10, 20])
    invariant.append([12, 19])
    invariant.append([900, 990])
    invariant.append([40, 60])
    invariant.append([0, 1])        
    mode_inv.append([0, invariant])
    print ("invariant ", invariant)
    print ("Mode invariant = ", mode_inv)
    mode_inv.append([1, invariant])
    mode_inv.append([2, invariant])
    print ("Mode invariant = ", mode_inv)
    '''

    #for each mode i
    mode_inv : list[list[tuple[float,float]]] = []
    for ids in P:   # This loop runs for each mode. Also, used to obtain Mode invariants
        x_pts = [ {dim + 1: Y[id0, dim] for dim in range(L_y)} for id0 in ids ] 

        invariant : list[tuple[float,float]] = []
        for var_dim in range(L_y):  # invariant consists of list of bounds on the variables. The order is maintained
            x_dim_list = list(map(itemgetter(var_dim+1), x_pts))
            upperBound = max(x_dim_list)
            lowerBound = min(x_dim_list)
            invariant.append((lowerBound, upperBound))

        mode_inv.append(invariant)

    # print("Mode-invariants =", mode_inv)
    return mode_inv
