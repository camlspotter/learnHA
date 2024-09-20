from sklearn import linear_model
import numpy as np
from hybridlearner.types import MATRIX
from .connection import ConnectionPoint

Assignment = tuple[MATRIX, # coeffs, 2d
                   MATRIX] # intercepts 1d

def compute_assignment(list_connection_pt : list[ConnectionPoint],
                       L_y : int,
                       Y : MATRIX) -> Assignment:
    """
    Type Annotation function. Type annotation is performed on the assignments based on the variable's type.

    :param list_connection_pt: is the connection triplet having (pre-end, end, start) point/position for a connection.
    :param L_y: is the dimension (input + output variables) of the system whose trajectory is being parsed.
    :param Y: contains the y_list values for all the points except the first and last M points (M is the order in BDF).
    :return: the coefficients and intercept values of the assignment equations.

    """
    x_pts = [ [ Y [ connection_pt.src_end, dim ] for dim in range(L_y) ]
              for connection_pt in list_connection_pt ]
    y_pts = [ [ Y [ connection_pt.dst_start, dim ] for dim in range(L_y) ]
              for connection_pt in list_connection_pt ]

    # print("x_pts =", x_pts)
    # print()
    # print("y_pts =", y_pts)

    lin_reg = linear_model.LinearRegression()  # with intercepts
    lin_reg = lin_reg.fit(x_pts, y_pts)

    return lin_reg.coef_, lin_reg.intercept_
