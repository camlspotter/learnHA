import unittest

from dataclasses import asdict
import json

from .annotation import *

class Test(unittest.TestCase):
    def test_parse_annotation(self) -> None:
        assert parse_annotation('continuous') == Continuous()
        assert parse_annotation('pool(1.2, 3, 9.0)') == Pool([1.2, 3, 9.0])
        assert parse_annotation('constant(3.4)') == Constant(3.4)

        assert unparse_annotation(parse_annotation('continuous')) == 'continuous'
        assert unparse_annotation(parse_annotation('pool(1.2, 3, 9.0)')) == 'pool(1.2, 3.0, 9.0)'
        assert unparse_annotation(parse_annotation('constant(3.4)')) == 'constant(3.4)'