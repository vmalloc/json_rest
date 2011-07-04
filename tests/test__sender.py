import unittest
from .test_utils import TestCase
from cStringIO import StringIO
from json_rest import sender as json_rest_sender
from json_rest import Raw
from json_rest.sentinels import NO_DATA
from json_rest.exceptions import JSONRestRequestException
import cjson
import forge
import httplib
import urllib2

class SenderInitializationTest(TestCase):
    def test__from_host_port(self):
        sender = json_rest_sender.JSONRestSender.from_host_port("example.com", 8080)
        self.assertEquals(sender.get_uri(), "http://example.com:8080")
    def test__from_host_port_suffix(self):
        sender = json_rest_sender.JSONRestSender.from_host_port("a", 80, "some/path")
        self.assertEquals(sender.get_uri(), "http://a:80/some/path")
    def test__subclassing(self):
        class NewSender(json_rest_sender.JSONRestSender):
            pass
        sender = NewSender("http://some/url")
        new_sender = sender.get_sub_resource("a/b")
        self.assertIsNot(sender, new_sender)
        self.assertIsInstance(new_sender, NewSender)

class SenderTest(TestCase):
    def setUp(self):
        super(SenderTest, self).setUp()
        self.uri = "http://www.bla.com/r/a/b"
        self.sender = json_rest_sender.JSONRestSender(self.uri)
        self.assertEquals(self.sender.get_uri(), self.uri)
        self.assertIs(json_rest_sender.urlopen, urllib2.urlopen)
        self.forge.replace(json_rest_sender, "urlopen")
    def test__get_sub_resource(self):
        sub_sender = self.sender.get_sub_resource('a/b')
        self.assertIsNot(sub_sender, self.sender)
        self.assertEquals(sub_sender.get_uri(), self.uri + '/a/b')
    def test__get(self):
        self._test__request('GET', return_data=dict(a=1, b=2))
    def test__post(self):
        self._test__request('POST', dict(a=1, b=2))
    def test__delete(self):
        self._test__request('DELETE')
    def test__put(self):
        self._test__request('PUT')
    def _test__request(self, method, send_data=NO_DATA, return_data=NO_DATA):
        for subpath in (None, 'a/b'):
            self._test__request_sending(method, send_data, return_data, subpath)
    def _test__request_sending(self, method, send_data, return_data, subpath):
        func = getattr(self.sender, method.lower())
        response_data = '' if return_data is NO_DATA else cjson.encode(return_data)
        expected_url = self.uri
        if subpath is not None:
            assert not subpath.startswith('/')
            expected_url += '/' + subpath

        self._expect_json_rest_request(method, expected_url, send_data).and_return(FakeResponse(httplib.OK, response_data, content_type='application/json'))

        with self.forge.verified_replay_context():
            args = []
            if subpath is not None:
                args.append(subpath)
            kwargs = {}
            if send_data is not NO_DATA:
                kwargs.update(data=send_data)
            result = func(*args, **kwargs)
        if return_data is NO_DATA:
            self.assertIs(result, NO_DATA)
        else:
            self.assertEquals(result, return_data)

    def _expect_json_rest_request(self, method, expected_url, send_data):
        def _verify_request(request):
            if send_data is NO_DATA:
                self.assertIsNone(request.get_header("Content-type"))
            else:
                self.assertEquals(request.get_data(), cjson.encode(send_data))
                self.assertEquals(request.get_header("Content-type"), "application/json")
            self.assertEqual(request.get_header("Accept"), "application/json")

            self.assertEquals(request.get_full_url(), expected_url)

        returned = json_rest_sender.urlopen(_make_request_predicate(method))
        returned.and_call_with_args(_verify_request)
        return returned

    def test__request_not_json_encoded(self):
        data = 'some_data'
        fake_response = FakeResponse(httplib.OK, data)
        self._expect_json_rest_request('GET', self.uri, NO_DATA).and_return(
            fake_response
            )
        with self.forge.verified_replay_context():
            result = self.sender.get()
        self.assertIsInstance(result, Raw)
        self.assertEquals(result, data)
    def test__http_error_json_encoded(self):
        self._test__http_error(json=True)
    def test__http_error_non_json_encoded(self):
        self._test__http_error(json=False)
    def _test__http_error(self, json):
        error_data = dict(a=1, b=2)
        code = 415 # just some code...
        headers = FakeHeaders()
        if json:
            headers._headers['content-type'] = 'application/json'
        send_data = dict(c=2, b=3)
        self._expect_json_rest_request('POST', self.uri, send_data).and_raise(
            urllib2.HTTPError(self.uri, code, 'msg', headers, StringIO(cjson.encode(error_data)))
            )
        with self.forge.verified_replay_context():
            with self.assertRaises(JSONRestRequestException) as caught:
                self.sender.post(data=send_data)
        exception = caught.exception
        self.assertEquals(exception.code, code)
        self.assertIs(exception.sent_data, send_data)
        self.assertEquals(exception.url, self.uri)
        if json:
            self.assertEquals(exception.received_data, error_data)
        else:
            self.assertIsInstance(exception.received_data, Raw)
            self.assertEquals(exception.received_data, cjson.encode(error_data))



class FakeResponse(object):
    def __init__(self, code, data='', content_type=None):
        super(FakeResponse, self).__init__()
        self.code = code
        self.data = StringIO(data)
        self.headers = FakeHeaders()
        if content_type is not None:
            # get() is done using lower() on the key....
            self.headers._headers['content-type'] = content_type
    def read(self):
        return self.data.read()

class FakeHeaders(object):
    def __init__(self):
        super(FakeHeaders, self).__init__()
        self._headers = {}
    def get(self, x):
        return self._headers.get(x.lower())

def _make_request_predicate(method):
    def _predicate(request):
        return request.get_method() == method
    return forge.Func(_predicate)
