import unittest
from hybridlearner.polynomial import *
from hybridlearner import astdsl


class Test(unittest.TestCase):
    def test_ncombs_of_degree(self) -> None:
        assert ncombs_of_degree(3, 1) == 4
        assert ncombs_of_degree(3, 2) == 10
        assert ncombs_of_degree(3, 3) == 20
        assert ncombs_of_degree(3, 4) == 35

    def test_build_polynomial(self) -> None:
        def f(
            variables: list[str], order: int, coeffs: list[float], must_be: str
        ) -> None:
            p = build_polynomial(variables, order, coeffs)
            assert (
                p.string == must_be
            ), f"Error: must_be: {must_be}  obtained: {p.string}"
            e = astdsl.parse_expr(p.string)
            va = expr_to_variable_annotated(e)
            coeffs2 = unbuild_variable_annotated(variables, order, va)
            assert (
                coeffs == coeffs2
            ), f"Error: coeffs: {coeffs}  obtained: {coeffs2}.  polynomial: {p.string}"

        f(['x', 'y'], 1, [1.0, 2.0, 3.0], "x * 1.0 + y * 2.0 + 3.0")
        f(
            ['x', 'y', 'z'],
            2,
            [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "x * x * 1.0 + x * y * 2.0 + x * z * 3.0 + y * y * 4.0 + y * z * 5.0 + z * z * 6.0 + x * 7.0 + y * 8.0 + z * 9.0 + 10.0",
        )
