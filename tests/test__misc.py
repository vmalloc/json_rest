from .test_utils import TestCase
from json_rest import NO_DATA, Raw
from json_rest.sender import RestRequest

class TestSentinels(TestCase):
    def test__sentinel_repr(self):
        self.assertEquals(repr(NO_DATA), str(NO_DATA))
        self.assertEquals(str(NO_DATA), '<NO_DATA>')
    def test__raw(self):
        self.assertEquals(Raw('bla'), Raw('bla'))
        self.assertFalse(Raw('bla') != Raw('bla'))
        for other in ['bla', 'b', Raw('bbb'), None, 2]:
            self.assertFalse(Raw('bla') == other )
            self.assertTrue(Raw('bla') != other)
class RestRequestTest(TestCase):
    def test__rest_request_repr_str(self):
        r = RestRequest("GET", "http://x.com/a/b/c")
        self.assertGreater(len(str(r)), 0)
