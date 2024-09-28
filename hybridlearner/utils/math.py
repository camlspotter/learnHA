import numpy as np
from numpy.typing import NDArray
import math


def permut(n: int, k: int) -> list[list[int]]:
    """
    Author: Amit Gurung
    :param self:
    :param n: the power of the multinomial
    :param k: the number of terms/variables in the multinomial
    :return: All the coefficients of the multinomial expansion of the form (a+b+c+ ... + k)^n
    """
    res = []
    myres: list[list[int]] = []

    def backtrack(start: int, comb: list[int]) -> None:
        sumEle = 0
        for x in range(0, len(comb)):
            sumEle += comb[x]

        if len(comb) == k and sumEle == n:
            # myres.append(comb.copy())   # appends at the end
            myres.insert(0, comb.copy())  # appends at the start
            # print(myres)
        if len(comb) == k:
            res.append(comb.copy())
            return
        # else:
        #     pass

        for i in range(start, n + 1):  # to include n
            comb.append(i)
            backtrack(start, comb)  # everytime the combination starts from 0
            comb.pop()

    backtrack(0, [])  # starts from 0
    # return res    # returns all the list without the constrain such that r1+r2+...+rk == n
    return myres  # returns all the list that satisfy the constrain such that r1+r2+...+rk == n


def factorial(i: int) -> int:
    if i == 0:
        return 1
    fact = 1
    for x in range(1, i + 1):
        fact *= x
    return fact


def compute_coeff(list_data: list[int]) -> float:
    """
    Author: Amit Gurung
    :param list_data:
    :return: coefficient using the formula n!/(r1! * r2! * ... * rk!). where r1+r2+...+rk == n
    """
    sum_n = 0
    fact_powers = 1
    for i in list_data:
        sum_n += i
        fact_powers *= factorial(i)
    coefficient_val = factorial(sum_n) / fact_powers
    return coefficient_val


def multinomial(vars: int, powers: int) -> list[tuple[float, list[int]]]:
    """
    Author: Amit Gurung
    :param vars: number of terms or variables
    :param powers: highest power
    :return: All the list of combinations/expansion of Multinomial along with the computed Coefficient of each term
     [coeff: double, followed by expansion_list]
    """
    comb_list = permut(powers, vars)
    # print(comb_list)
    return [(compute_coeff(data), data) for data in comb_list]


def mat_norm(A: NDArray[np.float64]) -> float:
    '''This is Euclidean norm'''
    return math.sqrt(np.square(A).sum())


def rel_diff(A: NDArray[np.float64], B: NDArray[np.float64]) -> float:
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
        return mat_norm(A - B)  # fixing division by zero error
    else:
        return mat_norm(A - B) / (mat_norm(A) + mat_norm(B))


def matrowex(matr: NDArray[np.float64], l: list[int]) -> NDArray[np.float64]:
    """Pick some rows of a matrix to form a new matrix."""
    rows = [matr[l[i]] for i in range(0, len(l))]
    return np.array(rows)


if __name__ == "__main__":
    dim = 3 + 1
    degree = 2
    combine_list = multinomial(dim, degree)
    print(combine_list)
