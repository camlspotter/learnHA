import unittest
from infer_ha.invariant import *

class Test(unittest.TestCase):
    def test_variable(self):
        for test in [
                "x",
                "xyz",
                "xy123",
                "xy_z_12_"
        ]:
            print(variable.parse_string(test))

    def test_inequality(self):
        for test in [
                "x <= 1",
                "x >= 1.23",
                ".12 >= y12",
                "0. <= y"
        ]:
            print(inequality.parse_string(test))
    

    def test_invariant(self):
        for test in [
                "1 <= x && x <= 1.23 && 0. <= y12 && y12 <= 2.3"
        ]:
            print(invariant.parse_string(test))
            print(check_invariant(invariant.parse_string(test)))
