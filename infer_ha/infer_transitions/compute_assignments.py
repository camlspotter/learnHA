from sklearn import linear_model
import numpy as np
from infer_ha.types import MATRIX

def compute_assignments(list_connection_pt : list[tuple[int,int,int]], L_y : int, Y : MATRIX) -> tuple[MATRIX, # coeffs, 2d
                                                                                              MATRIX # intercepts, 1d
                                                                                              ]:
    """
    Type Annotation function. Type annotation is performed on the assignments based on the variable's type.

    :param list_connection_pt: is the connection triplet having (pre-end, end, start) point/position for a connection.
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :return: the coefficients and intercept values of the assignment equations.

    """
    x_pts = []
    y_pts = []
    for connection_pt in list_connection_pt:
        # for id0 in connection_pt:  # Note: connection_pt now contains [pre_end, end, and start positions]
        # SOURCE-POINT: end-pt-position
        id0 = connection_pt[1]  # now index is [1] for end-posi
        x_pts.append([Y[id0, dim] for dim in range(L_y)])

        # DESTINATION-POINT: start-pt-position
        id0 = connection_pt[2]  # Now index is [2] for start_posi
        y_pts.append([Y[id0, dim] for dim in range(L_y)])

    # print("x_pts =", x_pts)
    # print()
    # print("y_pts =", y_pts)

    lin_reg = linear_model.LinearRegression()  # with intercepts
    lin_reg = lin_reg.fit(x_pts, y_pts)

    return lin_reg.coef_, lin_reg.intercept_
