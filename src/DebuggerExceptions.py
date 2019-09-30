#  DebuggerExceptions.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module contains the Exception classes for the Debugger connection

class BasicException(Exception):
    def __init__(self, msg):
        self.error_msg = msg

    def __str__(self):
        return self.error_msg

class DebuggerErrorMessage(BasicException):
    def __init__(self, msg):
        super().__init__(msg)

class DebuggingException(BasicException):
    def __init__(self, msg):
        super().__init__(msg)

class CompilerErrorMessage(BasicException):
    def __init__(self, msg):
        super().__init__(msg)
