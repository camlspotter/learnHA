import unittest
from hybridlearner.automaton import *


class Test(unittest.TestCase):
    def test_build_assignments(self):
        a = build_assignments(
            ["a", "b", "c"],
            ["a", "b", "c"],
            (
                np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
                np.array([10, 11, 12]),
            ),
        )
        assert str(a) == "{'a': Polynomial(string='a * 1.0 + b * 2.0 + c * 3.0 + 10.0'), 'b': Polynomial(string='a * 4.0 + b * 5.0 + c * 6.0 + 11.0'), 'c': Polynomial(string='a * 7.0 + b * 8.0 + c * 9.0 + 12.0')}"
        
