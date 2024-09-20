import unittest
from hybridlearner.invariant import *
from hybridlearner import parser

class Test(unittest.TestCase):
    def test_variable(self):
        for test in [
                "x",
                "xyz",
                "xy123",
                "xy_z_12_"
        ]:
            print(parser.variable.parse_string(test, parse_all=True))

    def test_inequality(self):
        for test in [
                "x <= 1",
                "x >= 1.23",
                ".12 >= y12",
                "0. <= y"
        ]:
            print(parser.inequality.parse_string(test, parse_all= True))
    

    def test_invariant(self):
        for test in [
                "1 <= x && x <= 1.23 && 0. <= y12 && y12 <= 2.3"
        ]:
            print(parser.invariant.parse_string(test))
            print(parser.check_invariant(parser.invariant.parse_string(test, parse_all= True)))
