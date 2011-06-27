class JSONRestRequestException(Exception):
    def __init__(self, method, url, code, sent_data, received_data):
        super(JSONRestRequestException, self).__init__()
        self.method = method
        self.url = url
        self.code = code
        self.sent_data = sent_data
        self.received_data = received_data

