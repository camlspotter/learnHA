import unittest
from hybridlearner.astdsl import *


class Test(unittest.TestCase):
    def test(self):
        print(Set([Value(1), Value(2)]))
        print(parse_expr('{1,2,3}'))

    def test_minus(self):
        assert (
            str(parse_expr('x * -12.0 + -1.9e-13'))
            == "BinOp(left=BinOp(left=Variable(id='x'), op='*', right=Value(value=-12.0)), op='+', right=Value(value=-1.9e-13))"
        )
        assert (
            unparse_expr(parse_expr('x * -12.0 + -1.9e-13')) == 'x * -12.0 + -1.9e-13'
        )
