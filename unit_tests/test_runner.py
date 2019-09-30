import unittest, sys

sys.path.append("src")
from SessionManagerTests import SessionManagerTests
from IOToolsTests import IOToolsTests
from LexerTests import LexerTests
from ArgParserTests import ArgParserTests
from SocketManagerTests import SocketManagerTests
from DebuggerTests import DebuggerTests
from TimerTests import TimerTests

if __name__ == '__main__':
    unittest.main()
