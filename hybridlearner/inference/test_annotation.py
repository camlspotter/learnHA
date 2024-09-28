import unittest


from .annotation import *
from hybridlearner.astdsl import parse_expr


class Test(unittest.TestCase):
    def test_parse_annotation(self) -> None:
        assert parse_annotation(parse_expr('continuous')) == Continuous()
        assert parse_annotation(parse_expr('pool(1.2, 3, 9.0)')) == Pool([1.2, 3, 9.0])
        assert parse_annotation(parse_expr('constant(3.4)')) == Constant(3.4)

        assert (
            unparse_annotation(parse_annotation(parse_expr('continuous')))
            == 'continuous'
        )
        assert (
            unparse_annotation(parse_annotation(parse_expr('pool(1.2, 3, 9.0)')))
            == 'pool(1.2, 3.0, 9.0)'
        )
        assert (
            unparse_annotation(parse_annotation(parse_expr('constant(3.4)')))
            == 'constant(3.4)'
        )
