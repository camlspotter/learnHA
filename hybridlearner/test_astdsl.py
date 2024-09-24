import unittest
from hybridlearner.astdsl import *


class Test(unittest.TestCase):
    def test(self):
        print(Set([Value(1), Value(2)]))
        print(parse_expr('{1,2,3}'))
