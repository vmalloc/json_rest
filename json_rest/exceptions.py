class JSONRestRequestException(Exception):
    def __init__(self, method, url, code, sent_headers, sent_data, received_headers, received_data):
        super(JSONRestRequestException, self).__init__()
        self.method = method
        self.url = url
        self.code = code
        self.sent_data = sent_data
        self.sent_headers = sent_headers
        self.received_data = received_data
        self.received_headers = received_headers

