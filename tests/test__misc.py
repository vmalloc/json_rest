import unittest
from json_rest.sentinels import NO_DATA

class TestSentinels(unittest.TestCase):
    def test__sentinel_repr(self):
        self.assertEquals(repr(NO_DATA), str(NO_DATA))
        self.assertEquals(str(NO_DATA), '<NO_DATA>')
