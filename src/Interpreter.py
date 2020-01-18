#  Interpreter.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
import threading
import Logging

from Session import Session

INTERPRETER_TIMEOUT = 60
logger = Logging.get_logger(__name__)

class Interpreter(Session):
    def __init__(self, code, session_id, session_manager):
        super().__init__(session_id, session_manager)
        self._create_process(code)

    def close(self):
        self.stop()

    def stop(self):
        with self._lock:
            if self._proc is not None:
                self._kill()

    def get_status(self):
        if self._proc != None and self._proc.poll() is None:
            return "running"
        else:
            return "terminated"

    @staticmethod
    def get_timeout():
        return INTERPRETER_TIMEOUT

    @staticmethod
    def reuse_session():
        return False

    def get_file_descriptors(self):
        return [self._proc.stdout.fileno()]
