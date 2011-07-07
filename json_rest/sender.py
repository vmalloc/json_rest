import httplib
import logging
import cjson
from urllib2 import urlopen
from urllib2 import HTTPError
from urllib2 import Request as URLLibRequest
from .exceptions import JSONRestRequestException
from sentinels import Sentinel
from .raw import Raw

NO_DATA = Sentinel("NO_DATA")

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
    def send_request(self, method, uri, data):
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

    def _get_send_data_and_content_type(self, send_data):
        if isinstance(send_data, Raw):
            return send_data.data, None
        if send_data is NO_DATA:
            return NO_DATA, None
        return cjson.encode(send_data), "application/json"

    def send_request(self, method, uri, data):
        request = self._create_request(method, data, uri)
        _logger.debug("Sending request: %s", request)
        try:
            response = urlopen(request)
        except HTTPError, e:
            error_data = e.fp.read()
            _logger.debug("Got response: code=%s data=%r", e.code, error_data)
            if e.headers.get('content-type') == 'application/json':
                error_data = cjson.decode(error_data)
            else:
                error_data = Raw(error_data)
            raise JSONRestRequestException(
                method, request.get_full_url(), e.code,
                sent_headers=request.headers,
                sent_data=data, received_headers=e.headers, received_data=error_data)
        response_data = response.read()
        _logger.debug("Got response: code=%s data=%r", response.code, response_data)
        return self._build_response_data(response, response_data)
    def _build_response_data(self, response, response_data):
        if response.code == httplib.NO_CONTENT:
            return NO_DATA
        if response.headers.get('Content-type') == 'application/json':
            return cjson.decode(response_data)
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
