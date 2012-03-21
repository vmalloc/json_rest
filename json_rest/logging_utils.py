from logging import Handler
class NullHandler(Handler):
    """
    NullHandler from Python 2.7 - doesn't exist on Python 2.6
    """
    def handle(self, record):
        pass
    def emit(self, record):
        pass
    def createLock(self):
        self.lock = None
