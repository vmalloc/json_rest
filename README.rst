Overview
--------
json_rest is a set of utilities for talking to JSON/REST web services via Python.

JSONRestSender
==============
This is a small utility for issuing the requests and parsing responses. It takes care of encoding the data sent to JSON, and decoding the responses (assuming Content-type is *application/json*)::

  >>> from json_rest import JSONRestSender
  >>> sender = JSONRestSender(SERVER_ADDRESS)
  >>> sender.set_header('X-some-header', 'some-value')
  >>> sender.get('path/to/resource')
  {'hello': 'world'}
  >>> sender.post('path/to/resource', dict(some='data'), headers={'X-additional-header' : 'value'})
  {'hello': 'world'}
  >>> response = sender.send_request_get_response_object('GET', 'x/y')
  >>> response.get_code()
  200
  >>> response.get_result()
  {'hello': 'world'}
