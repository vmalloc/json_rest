Overview
--------
json_rest is a set of utilities for talking to JSON/REST web services via Python.

JSONRestSender
==============
This is a small utility for issuing the requests and parsing responses. It takes care of encoding the data sent to JSON, and decoding the responses (assuming Content-type is *application/json*)::

  >>> from json_rest import JSONRestSender
  >>> sender = JSONRestSender("http://www.example.com/a/b")
  >>> decoded_data = sender.get('path/to/resource')
  >>> decoded_data = sender.post('path/to/resource', dict(some='data'))
