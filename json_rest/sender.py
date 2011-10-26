import httplib
import logging
import cjson
from urllib2 import urlopen
from urllib2 import HTTPError, URLError
from urllib2 import Request as URLLibRequest
from .exceptions import JSONRestRequestException, JSONRestDecodeException
from .raw import Raw
from .no_data import NO_DATA

_logger = logging.getLogger("json_rest")
_logger.addHandler(logging.NullHandler())

class AbstractJSONRestSender(object):
    def post(self, uri=None, data=NO_DATA):
        return self.send_request('POST', uri, data)
    def get(self, uri=None):
        return self.send_request('GET', uri, NO_DATA)
    def put(self, uri=None, data=NO_DATA):
        return self.send_request('PUT', uri, data)
    def delete(self, uri=None):
        return self.send_request('DELETE', uri, NO_DATA)
    def send_request(self, method, uri, data=NO_DATA):
        returned_response = self.send_request_get_response_object(method, uri, data)
        return returned_response.get_result()
    def send_request_get_response_object(self, method, uri, data=NO_DATA):
        raise NotImplementedError() # pragma: no cover

class JSONRestSender(AbstractJSONRestSender):
    def __init__(self, uri):
        super(JSONRestSender, self).__init__()
        self._uri = uri
    @classmethod
    def from_host_port(cls, host, port, suffix=''):
        returned = cls("http://{}:{}".format(host, port))
        if suffix:
            returned.append_uri_fragment(suffix)
        return returned
    def get_uri(self):
        return self._uri
    def append_uri_fragment(self, fragment):
        self._uri = _urljoin(self._uri, fragment)
    def get_sub_resource(self, resource):
        returned = type(self)(self._uri)
        returned.append_uri_fragment(resource)
        return returned
    def _create_request(self, method, send_data, uri):
        full_uri = self._uri
        if uri is not None:
            full_uri = _urljoin(full_uri, uri)
        send_data, content_type = self._get_send_data_and_content_type(send_data)
        request = RestRequest(method, full_uri, send_data)
        request.add_header("Accept", "application/json")
        if content_type is not None:
            request.add_header('Content-type', 'application/json')
        return request
    def send_request_get_response_object(self, method, uri, data=NO_DATA):
        request = self._create_request(method, data, uri)
        _logger.debug("Sending request: %s", request)
        try:
            response = urlopen(request)
        except HTTPError as response:
            error_data = self._parse_response_data(response.code, response.fp.read(), response.headers, safe=True)
            _logger.debug("Got response: code=%s data=%r", response.code, error_data)
            raise JSONRestRequestException.from_request_and_response(request, response, data, error_data)
        except URLError as e:
            raise JSONRestRequestException.from_request_and_exception(request, e, data)
        response_data = response.read()
        _logger.debug("Got response: code=%s data=%r", response.code, response_data)
        try:
            json_data = self._parse_response_data(response.code, response_data, response.headers)
        except cjson.DecodeError as decode_err:
            raise JSONRestDecodeException.from_request_and_response(request, response, data,
                                                                    Raw(response_data), repr(decode_err))
        return RestResponse(code=response.code, result=json_data)
    def _get_send_data_and_content_type(self, send_data):
        if isinstance(send_data, Raw):
            return send_data.data, None
        if send_data is NO_DATA:
            return None, None
        return cjson.encode(send_data), "application/json"
    def _parse_response_data(self, code, response_data, response_headers, safe=False):
        if code == httplib.NO_CONTENT:
            return NO_DATA
        if response_headers.get('content-type') == 'application/json':
            try:
                return cjson.decode(response_data)
            except cjson.DecodeError:
                if not safe: raise
                return Raw(response_data)
        return Raw(response_data)

def _urljoin(*urls):
    "Like urlparse's urljoin, only more forgiving for lack of slashes"
    returned = None
    for url in urls:
        if returned is None:
            returned = url
        else:
            if not returned.endswith('/') and not url.startswith('/'):
                returned += '/'
            returned += url
    return returned

class RestRequest(URLLibRequest):
    def __init__(self, method, *args, **kwargs):
        URLLibRequest.__init__(self, *args, **kwargs) # ARRGH old-style classes!
        self._method = method
    def get_method(self):
        return self._method
    def __repr__(self):
        return "<%s %s <-- %r>" % (self._method, self.get_full_url(), self.get_data())

class RestResponse(object):
    def __init__(self, code, result):
        super(RestResponse, self).__init__()
        self._code = code
        self._result = result
    def get_code(self):
        return self._code
    def get_result(self):
        return self._result
