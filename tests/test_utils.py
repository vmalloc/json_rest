from forge import Forge
try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.forge = Forge()
    def tearDown(self):
        self.forge.verify()
        self.forge.restore_all_replacements()
        super(TestCase, self).tearDown()
