import cjson
from urllib2 import urlopen
from urllib2 import HTTPError
from urllib2 import Request as URLLibRequest
from .exceptions import JSONRestRequestException
from .sentinels import NO_DATA
from .raw import Raw

class JSONRestSender(object):
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
        returned = JSONRestSender(self._uri)
        returned.append_uri_fragment(resource)
        return returned
    def post(self, uri=None, data=NO_DATA):
        return self._request('POST', uri, data)
    def get(self, uri=None):
        return self._request('GET', uri, NO_DATA)
    def put(self, uri=None, data=NO_DATA):
        return self._request('PUT', uri, data)
    def delete(self, uri=None):
        return self._request('DELETE', uri, NO_DATA)
    def _request(self, method, uri, data):
        if data is NO_DATA:
            send_data = ''
        else:
            send_data = cjson.encode(data)
        full_uri = self._uri
        if uri is not None:
            full_uri = _urljoin(full_uri, uri)
        request = RestRequest(method, full_uri, send_data)
        request.add_header("Accept", "application/json")
        if send_data:
            request.add_header('Content-type', 'application/json')
        try:
            response = urlopen(request)
        except HTTPError, e:
            error_data = e.fp.read()
            if e.headers.get('content-type') == 'application/json':
                error_data = cjson.decode(error_data)
            else:
                error_data = Raw(error_data)
            raise JSONRestRequestException(method, full_uri, e.code, data, error_data)
        return self._build_response_data(response)
    def _build_response_data(self, response):
        data = response.read()
        if data:
            if response.headers.get('Content-type') == 'application/json':
                return cjson.decode(data)
            else:
                return Raw(data)
        return NO_DATA

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