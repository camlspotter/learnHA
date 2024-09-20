import unittest
from hybridlearner import parser

class Test(unittest.TestCase):
    def test_delimited_list(self):
        # list(..) is required 
        assert list(parser.delimited_list(parser.variable, delim= ',').parse_string('', parse_all= True)) == []

        # list(..) is required 
        assert list(parser.delimited_list(parser.variable, delim= ',').parse_string('a , b, c', parse_all= True)) == ['a', 'b', 'c']

        

        
