import itertools
import unittest
from .test_utils import TestCase
from cStringIO import StringIO
from json_rest import sender as json_rest_sender
from json_rest import Raw
from json_rest import NO_DATA
from json_rest.exceptions import *
import base64
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
    def test__set_basic_authorization(self):
        sender = json_rest_sender.JSONRestSender.from_host_port("a", 80)
        sender.set_basic_authorization("username", "password")
        self.assertEquals(sender.get_headers()['Authorization'], 'Basic ' + base64.encodestring("username:password").rstrip())
    def test__subclassing(self):
        class NewSender(json_rest_sender.JSONRestSender):
            pass
        sender = NewSender("http://some/url")
        new_sender = sender.get_sub_resource("a/b")
        self.assertIsNot(sender, new_sender)
        self.assertIsInstance(new_sender, NewSender)
    def test__timeout_passing(self):
        timeout_seconds=127
        sender = json_rest_sender.JSONRestSender.from_host_port("www.example.com", 8080, default_timeout_seconds=timeout_seconds)
        self.assertEquals(sender._default_timeout_seconds, timeout_seconds)

class SenderTest(TestCase):
    def setUp(self):
        super(SenderTest, self).setUp()
        self.uri = "http://www.bla.com/r/a/b"
        self.sender = json_rest_sender.JSONRestSender(self.uri)
        self.headers = [('X-setup-header-1', 'value1'), ('X-setup-header-2', 'value2')]
        for header_name, header_value in self.headers:
            self.sender.set_header(header_name, header_value)
        self.assertEquals(self.sender.get_uri(), self.uri)
        self.assertIs(json_rest_sender.urlopen, urllib2.urlopen)
        self.forge.replace(json_rest_sender, "urlopen")
    def test__urlerror_exception_mapping(self):
        self._expect_json_rest_request("GET", self.uri, NO_DATA).and_raise(urllib2.URLError('reason'))
        self.forge.replay()
        with self.assertRaises(JSONRestRequestException):
            self.sender.get()
    def test__get_sub_resource(self):
        sub_sender = self.sender.get_sub_resource('a/b')
        self.assertIsNot(sub_sender, self.sender)
        self.assertEquals(sub_sender.get_uri(), self.uri + '/a/b')
    def test__get(self):
        self._test__request('GET', return_data=dict(a=1, b=2))
    def test__empty_content_and_json_encoded(self):
        send_data = dict(a=1, b=2)
        self._expect_json_rest_request('POST', self.uri, send_data).and_return(FakeResponse(httplib.OK, '', content_type='application/json'))
        self.forge.replay()
        with self.assertRaises(JSONRestDecodeException):
            self.sender.post(data=send_data)
    def test__empty_content_not_json_encoded(self):
        send_data = dict(a=1, b=2)
        self._expect_json_rest_request('POST', self.uri, send_data).and_return(FakeResponse(httplib.OK, ''))
        self.forge.replay()
        self.assertEquals(Raw(''), self.sender.post(data=send_data))
    def test__post(self):
        self._test__request('POST', dict(a=1, b=2))
    def test__post_with_headers(self):
        self._test__request('POST', dict(a=1, b=2), headers=[('X-some-header', 'some_value'), ('X-another-header', 'another_value')])
    def test__post_raw_data(self):
        self._test__request('POST', Raw('data'))
    def test__delete(self):
        self._test__request('DELETE')
    def test__put(self):
        self._test__request('PUT')
    def _test__request(self, method, send_data=NO_DATA, return_data=NO_DATA, headers=()):
        for subpath in (None, 'a/b'):
            self._test__request_sending(method, send_data, return_data, subpath, headers=headers)
    def _test__request_sending(self, method, send_data, return_data, subpath, headers=()):
        func = getattr(self.sender, method.lower())
        if return_data is NO_DATA:
            response_data = ''
            response_code = httplib.NO_CONTENT
        else:
            response_data = cjson.encode(return_data)
            response_code = httplib.OK
        expected_url = self.uri
        if subpath is not None:
            assert not subpath.startswith('/')
            expected_url += '/' + subpath
        self._expect_json_rest_request(method, expected_url, send_data, headers=headers).and_return(FakeResponse(response_code, response_data, content_type='application/json'))

        with self.forge.verified_replay_context():
            args = []
            if subpath is not None:
                args.append(subpath)
            kwargs = {}
            kwargs.update(headers=headers)
            if send_data is not NO_DATA:
                kwargs.update(data=send_data)
            result = func(*args, **kwargs)
        if return_data is NO_DATA:
            self.assertIs(result, NO_DATA)
        else:
            self.assertEquals(result, return_data)

    def _expect_json_rest_request(self, method, expected_url, send_data, headers=(), timeout=None):
        def _verify_request(request, *args, **kwargs):
            if send_data is NO_DATA or isinstance(send_data, Raw):
                self.assertIsNone(request.get_header("Content-type"))
            else:
                self.assertEquals(request.get_data(), cjson.encode(send_data))
                self.assertEquals(request.get_header("Content-type"), "application/json")
            if isinstance(send_data, Raw):
                self.assertEquals(request.get_data(), send_data.data)
            for expected_header_name, expected_header_value in itertools.chain(headers, self.headers):
                self.assertEquals(request.get_header(expected_header_name), expected_header_value)
            self.assertEqual(request.get_header("Accept"), "application/json")
            self.assertEquals(request.get_full_url(), expected_url)

        expected_kwargs = {}
        if timeout is not None:
            expected_kwargs.update(timeout=timeout)
        returned = json_rest_sender.urlopen(_make_request_predicate(method), **expected_kwargs)
        returned.and_call_with_args(_verify_request)
        return returned
    def test__request_timeout(self):
        timeout = 667
        fake_response = FakeResponse(httplib.OK, '')
        self._expect_json_rest_request('GET', self.uri, NO_DATA, timeout=timeout).and_return(fake_response)
        with self.forge.verified_replay_context():
            result = self.sender.get(timeout=timeout)
    def test__request_not_json_encoded(self):
        data = 'some_data'
        fake_response = FakeResponse(httplib.OK, data)
        self._expect_json_rest_request('GET', self.uri, NO_DATA).and_return(
            fake_response
            )
        with self.forge.verified_replay_context():
            result = self.sender.get()
        self.assertIsInstance(result, Raw)
        self.assertEquals(result.data, data)
    def test__request_json_encoded_with_charset(self):
        expected_result = dict(a=1, b=2)
        data = cjson.encode(expected_result)
        fake_response = FakeResponse(httplib.OK, data, 'application/json;charset=UTF-8')
        self._expect_json_rest_request('GET', self.uri, NO_DATA).and_return(
            fake_response
            )
        with self.forge.verified_replay_context():
            result = self.sender.get()
        self.assertEquals(result, expected_result)
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
        #make sure the exception is printable
        self.assertIsInstance(str(exception), basestring)
        self.assertIsInstance(repr(exception), basestring)
        self.assertEquals(exception.code, code)
        self.assertIs(exception.sent_data, send_data)
        self.assertEquals(exception.url, self.uri)
        if json:
            self.assertEquals(exception.received_data, error_data)
        else:
            self.assertIsInstance(exception.received_data, Raw)
            self.assertEquals(exception.received_data.data, cjson.encode(error_data))

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
