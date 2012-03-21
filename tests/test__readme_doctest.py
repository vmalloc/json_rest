from unittest import TestCase
import httplib
import cjson
import os
import doctest
import multiprocessing
import SimpleHTTPServer
import SocketServer

class RestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def _handle(self):
        self.send_response(httplib.OK)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(cjson.encode(dict(hello="world")))
    do_GET = do_POST = _handle
    def log_message(self, *_, **__):
        pass # QUIET!

class ReadMeDocTest(TestCase):
    def setUp(self):
        super(ReadMeDocTest, self).setUp()
        httpd = SocketServer.TCPServer(("127.0.0.1", 0), RestHandler)
        self.server_process = multiprocessing.Process(target=httpd.serve_forever)
        self.server_process.daemon = True
        self.server_process.start()
        self.server_address = "http://{0}:{1}".format(*httpd.server_address)
    def tearDown(self):
        self.server_process.terminate()
        super(ReadMeDocTest, self).tearDown()
    def test__readme_doctests(self):
        readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "README.rst"))
        with open(readme_path, "rb") as readme_file:
            readme_contents = readme_file.read().replace("SERVER_ADDRESS", repr(self.server_address))
        test = doctest.DocTestParser().get_doctest(readme_contents, {}, "<readme>", readme_path, 0)
        runner = doctest.DocTestRunner()
        runner.run(test)
        self.assertEquals(runner.failures, 0, "Doctests failed!")
