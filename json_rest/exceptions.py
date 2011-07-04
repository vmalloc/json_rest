import httplib

_EXCEPTION_REPR_TEMPLATE = """HTTP Error {e.code} ({e.code_string}):
  METHOD: {e.method}
  URL: {e.url}
  SENT DATA: {e.sent_data}
  GOT DATA: {e.received_data}
"""

class JSONRestRequestException(Exception):
    def __init__(self, method, url, code, sent_headers, sent_data, received_headers, received_data):
        super(JSONRestRequestException, self).__init__()
        self.method = method
        self.url = url
        self.code = code
        self.code_string = httplib.responses.get(code, "?")
        self.sent_data = sent_data
        self.sent_headers = sent_headers
        self.received_data = received_data
        self.received_headers = received_headers
    def __repr__(self):
        return _EXCEPTION_REPR_TEMPLATE.format(e=self)
    def __str__(self):
        return repr(self)
