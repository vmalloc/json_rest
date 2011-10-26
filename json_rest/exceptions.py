import httplib
from .no_data import NO_DATA

_EXCEPTION_REPR_TEMPLATE = """HTTP {e.code} ({e.code_string}):
  METHOD: {e.method}
  URL: {e.url}
  SENT DATA: {e.sent_data}
  GOT DATA: {e.received_data}
"""

class JSONRestRequestException(Exception):
    def __init__(self, method, url, code, sent_headers, sent_data, received_headers, received_data, msg=None):
        super(JSONRestRequestException, self).__init__()
        self.method = method
        self.url = url
        self.code = code
        self.code_string = httplib.responses.get(code, "?")
        self.sent_data = sent_data
        self.sent_headers = sent_headers
        self.received_data = received_data
        self.received_headers = received_headers
        self.msg = msg
    @classmethod
    def from_request_and_exception(cls, request, exception, sent_data):
        return cls(
            method=request.get_method(),
            url=request.get_full_url(),
            code=None,
            sent_headers=request.headers,
            sent_data=sent_data,
            received_headers=None,
            received_data=NO_DATA,
            msg=str(exception),
            )
    @classmethod
    def from_request_and_response(cls, request, response, sent_data, received_data, msg=None):
        return cls(
            method=request.get_method(),
            url=request.get_full_url(),
            code=response.code,
            sent_headers=request.headers,
            sent_data=sent_data,
            received_headers=response.headers,
            received_data=received_data,
            msg=msg)
    def __repr__(self):
        return _EXCEPTION_REPR_TEMPLATE.format(e=self)
    def __str__(self):
        return repr(self)

class JSONRestDecodeException(JSONRestRequestException):
    pass
