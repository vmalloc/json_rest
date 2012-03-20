import os
import platform
import itertools
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "json_rest", "__version__.py")) as version_file:
    exec(version_file.read())

_INSTALL_REQUIREMENTS = ["python-cjson", "pyforge", "sentinels"]
if platform.python_version() < '2.7':
    _INSTALL_REQUIREMENTS.append('unittest2')

setup(name="json_rest",
      classifiers = [
          "Development Status :: 4 - Beta",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: BSD License",
          "Programming Language :: Python :: 2.7",
          ],
      description="Utility for REST/JSON based web services",
      license="BSD",
      author="Rotem Yaari",
      author_email="vmalloc@gmail.com",
      version=__version__,
      packages=find_packages(exclude=["tests"]),
      install_requires=_INSTALL_REQUIREMENTS,
      scripts=[],
      )
