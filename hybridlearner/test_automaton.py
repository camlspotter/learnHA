import unittest
from hybridlearner.automaton import *


class Test(unittest.TestCase):
    def test_build_polynomial(self):
        assert (
            str(build_polynomial(["a", "b", "c"], [1, 2, 3, 4]))
            == "{'a': 1, 'b': 2, 'c': 3, '1': 4}"
        ), "build_guard bug"

    def test_build_assignments(self):
        assert (
            str(
                build_assignments(
                    ["a", "b", "c"],
                    ["a", "b", "c"],
                    (
                        np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                        np.array([10, 11, 12]),
                    ),
                )
            )
            == "{'a': {'a': np.int64(1), 'b': np.int64(2), 'c': np.int64(3), '1': np.int64(10)}, 'b': {'a': np.int64(4), 'b': np.int64(5), 'c': np.int64(6), '1': np.int64(11)}, 'c': {'a': np.int64(7), 'b': np.int64(8), 'c': np.int64(9), '1': np.int64(12)}}"
        )
