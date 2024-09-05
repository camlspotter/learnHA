import unittest
from infer_ha.range import *

class Test(unittest.TestCase):
    def test_range(self) -> None:
        assert Range(1,2).contains(1.5), "Range.contains failure"
        ex_Range : Range = Range(1, 2)
        assert str(ex_Range) == "Range(min=1.0, max=2.0)", "Range bug:" + str(ex_Range)
        ex_Range2 : Range = Range(min=1, max=2)
        assert str(ex_Range2) == "Range(min=1.0, max=2.0)", "Range bug" + str(ex_Range)
