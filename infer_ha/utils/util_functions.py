'''
Contains all the helper functions used in the project infer_ha

'''


import numpy as np
from numpy.typing import NDArray
import math

def mat_norm(A : NDArray[np.float64]) -> float:
    ''' This is Euclidean norm '''
    return math.sqrt(np.square(A).sum())


def rel_diff(A : NDArray[np.float64], B : NDArray[np.float64]) -> float:
    """
    Computes a relative difference between A and B data structure
    @param A: can be a matrix (list of list) or numpy array.
    @param B: can be a matrix (list of list) or numpy array.
    @return:
        Relative difference between A and B.
        We simply return norm(A - B) if norm(A) + norm(B) == 0
        Here we consider the Euclidean norm.
    """
    if (mat_norm(A) + mat_norm(B)) == 0:
        return mat_norm(A - B)    # fixing division by zero error
    else:
        return mat_norm(A - B) / (mat_norm(A) + mat_norm(B))


def matrowex(matr : NDArray[np.float64], l : list[int]) -> NDArray[np.float64]:
    """Pick some rows of a matrix to form a new matrix."""
    rows = [matr[l[i]] for i in range(0, len(l))]
    return np.array(rows)


