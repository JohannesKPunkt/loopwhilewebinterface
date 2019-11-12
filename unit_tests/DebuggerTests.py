#  DebuggerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
import time, os

import tests_common
from Debugger import Debugger, DebuggerTelegram, TelegramType, DebuggerState
from DebuggerExceptions import DebuggerErrorMessage, CompilerErrorMessage, DebuggingException
from SessionManager import SessionManager

class DebuggerTests(unittest.TestCase):
    _next_session = 0
    @staticmethod
    def _next_session_id():
        sess_id = DebuggerTests._next_session
        DebuggerTests._next_session = sess_id+1
        return "testrun_" + str(sess_id)
        
    @staticmethod
    def write_to_process(proc, command):
        to_write = (command + "\n").encode()
        proc.stdin.write(to_write)
        proc.stdin.flush()

    @staticmethod
    def setUpClass():
        DebuggerTests._session_manager = SessionManager("user_src", 20)

    @staticmethod
    def tearDownClass():
        DebuggerTests._session_manager.shutdown()

    def test_parse_debugger_output(self):
        print("\n== start test_parse_debugger_output ==")
        # Test valid telegrams
        obj = Debugger.parse_debugger_output("""2 6 -1 [{"file":"/somefolder/test123.lw","line":6,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":2}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}]# Stepped.""")
        self.assertTrue(isinstance(obj, DebuggerTelegram))
        self.assertEqual(obj.ttype, TelegramType.STEPPED)
        self.assertEqual(obj.line_no, 6)
        self.assertEqual(obj.breakpoint_no, -1)
        self.assertEqual(obj.data, [{"file":"/somefolder/test123.lw","line":6,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":2}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}])

        obj = Debugger.parse_debugger_output("""0 7 1 [{"file":"C:\\\\\\\\somefolder\\\\test123.lw","line":7,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":0}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}]# Breakpoint 1 reached.""")
        self.assertTrue(isinstance(obj, DebuggerTelegram))
        self.assertEqual(obj.ttype, TelegramType.AT_BREAKPOINT)
        self.assertEqual(obj.line_no, 7)
        self.assertEqual(obj.breakpoint_no, 1)
        self.assertEqual(obj.data, [{"file":"C:\\\\somefolder\\test123.lw","line":7,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":0}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}])
        
        obj = Debugger.parse_debugger_output("""0 5 0 [{"file":"/somefolder/test123.lw","line":5,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":0}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}]# Breakpoint 0 reached.""")
        self.assertTrue(isinstance(obj, DebuggerTelegram))
        self.assertEqual(obj.ttype, TelegramType.AT_BREAKPOINT)
        self.assertEqual(obj.line_no, 5)
        self.assertEqual(obj.breakpoint_no, 0)
        self.assertEqual(obj.data, [{"file":"/somefolder/test123.lw","line":5,"macro":"multiply","bindings":[{"VarType":"input","Ident":"x","Val":5},{"VarType":"input","Ident":"y","Val":2},{"VarType":"output","Ident":"z","Val":0}]},{"file":"/somefolder/test123.lw","line":13,"macro":"root","bindings":[{"VarType":"input","Ident":"i0","Val":5},{"VarType":"output","Ident":"o0","Val":0}]}])

        obj = Debugger.parse_debugger_output("""1 7 1# Breakpoint 1 set.""")
        self.assertTrue(isinstance(obj, DebuggerTelegram))
        self.assertEqual(obj.ttype, TelegramType.BREAKPOINT_SET)
        self.assertEqual(obj.line_no, 7)
        self.assertEqual(obj.breakpoint_no, 1)
        self.assertIsNone(obj.data)

        # Test debugger error messages
        occurred = False
        try:
            Debugger.parse_debugger_output("""Unknown command.""")
        except DebuggerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, "Unknown command")
        except Exception as e:
            print(type(e))
            self.fail("Unexcepted exception of type " + str(type(e)) + ": " + str(e))
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            Debugger.parse_debugger_output("""Program is already running.""")
        except DebuggerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, "Program is already running")
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            Debugger.parse_debugger_output("""No Statement in line 1000.""")
        except DebuggerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, "No Statement in line 1000")
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            Debugger.parse_debugger_output("""Maximum number of breakpoints reached, can not set more breakpoints.""")
        except DebuggerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, "Maximum number of breakpoints reached, can not set more breakpoints")
        self.assertTrue(occurred, "Exception has not been raised.")

        # TODO: test compiler error messages
        occurred = False
        try:
            in_str = """2019/09/14 20:58:38 unexpected def in line 4, pos 1.
2019/09/14 20:58:38 def multiply:
2019/09/14 20:58:38 ^ unexpected token"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:08:06 unexpected == in line 5, pos 8.
2019/09/14 21:08:06   if x == 0 do
2019/09/14 21:08:06        ^ unexpected token"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:09:08 unexpected do, expected then in line 5, pos 13.
2019/09/14 21:09:08   if x != 0 do
2019/09/14 21:09:08             ^ unexpected token"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:09:28 unexpected - in line 6, pos 20.
2019/09/14 21:09:28     z := multiply(x-1, y);
2019/09/14 21:09:28                    ^ unexpected token"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:09:51 unexpected enddo, expected ';' in line 11, pos 3.
2019/09/14 21:09:51   enddo
2019/09/14 21:09:51   ^ unexpected token"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:10:13 Undeclared variable 'h' in line 6, file /somefolder/someothertest.lw.
"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        occurred = False
        try:
            in_str = """2019/09/14 21:11:35 Found cyclic dependency in macro definitions, aborting:
2019/09/14 21:11:35 multiply -> multiply"""
            Debugger.parse_debugger_output(in_str)
        except CompilerErrorMessage as e:
            occurred = True
            self.assertEqual(e.error_msg, in_str)
        self.assertTrue(occurred, "Exception has not been raised.")

        # TODO: test parse errors

    # Test debugging of test program simple.lw
    def test_program_simple1(self):
        print("\n== start test_program_simple1 ==")
        with open("test_programs/simple.lw", "r") as input_file:
            code = input_file.read()
        sess_id = self._next_session_id()
        input_file_path = os.path.abspath(DebuggerTests._session_manager.get_input_filename(sess_id))
        d = Debugger(code, sess_id, DebuggerTests._session_manager)
        print("setup breakpoints")
        d.set_breakpoint(6)
        d.set_breakpoint(8)
        d.set_breakpoint(9)
        self.assertEqual(d.get_breakpoints(), {6, 8, 9})
        print("call d.run()")
        d.run()

        
        # set input i0=2, i1=3
        d.process_user_input("2")
        d.process_user_input("3")

        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":6,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":2},
                                      {"VarType":"input","Ident":"i1","Val":3},
                                      {"VarType":"output","Ident":"o0","Val":0},
                                      {"VarType":"auxiliary","Ident":"tmp","Val":0}]}])

        print("resume after first breakpoint")
        #TODO get stacktrace and assert
        d.resume()
        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":8,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":2},
                                      {"VarType":"input","Ident":"i1","Val":3},
                                      {"VarType":"output","Ident":"o0","Val":0},
                                      {"VarType":"auxiliary","Ident":"tmp","Val":6}]}])

        #TODO stacktrace
        print("step after second breakpoint")
        d.step_into()
        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":9,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":2},
                                      {"VarType":"input","Ident":"i1","Val":3},
                                      {"VarType":"output","Ident":"o0","Val":0},
                                      {"VarType":"auxiliary","Ident":"tmp","Val":8}]}])

        print("resume to finish execution")
        d.resume()

        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.NOTSTARTED)

    # Test debugging of test program simple.lw with setting and 
    # removing breakpoints after run()
    def test_program_simple2(self):
        print("\n== start test_program_simple2 ==")
        with open("test_programs/simple.lw", "r") as input_file:
            code = input_file.read()
        sess_id = self._next_session_id()
        input_file_path = os.path.abspath(DebuggerTests._session_manager.get_input_filename(sess_id))
        d = Debugger(code, sess_id, DebuggerTests._session_manager)
        print("setup breakpoints")
        d.set_breakpoint(7)
        d.set_breakpoint(10)        
        self.assertEqual(d.get_breakpoints(), {7, 10})
        print("call d.run()")
        d.run()

        # set input i0=5, i1=6
        d.process_user_input("5")
        d.process_user_input("6")

        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":7,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":5},
                                      {"VarType":"input","Ident":"i1","Val":6},
                                      {"VarType":"output","Ident":"o0","Val":0},
                                      {"VarType":"auxiliary","Ident":"tmp","Val":11}]}])

        print("add new breakpoint")
        d.set_breakpoint(9)
        self.assertEqual(d.get_breakpoints(), {7, 9, 10})
        print("remove old breakpoint")
        d.remove_breakpoint(10)
        self.assertEqual(d.get_breakpoints(), {7, 9})

        print("resume after first breakpoint. Waiting for the debugger to stop."
              + " If this testcase does not terminate, it might be stuck in an infinite loop.")
        d.resume()
        while d.poll_state() != DebuggerState.PAUSED:
            pass
        self.assertEqual(d.get_breakpoints(), {7, 9})
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":9,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":5},
                                      {"VarType":"input","Ident":"i1","Val":6},
                                      {"VarType":"output","Ident":"o0","Val":0},
                                      {"VarType":"auxiliary","Ident":"tmp","Val":14}]}])

        d.resume()

        time.sleep(1)
        self.assertEqual(d.poll_state(), DebuggerState.NOTSTARTED)

    # Test debugging of test program loop.lw to check debugger state
    # after resume in a long enduring loop
    def test_program_loop1(self):
        print("\n== start test_program_loop1 ==")
        with open("test_programs/loop.lw", "r") as input_file:
            code = input_file.read()
        sess_id = self._next_session_id()
        input_file_path = os.path.abspath(DebuggerTests._session_manager.get_input_filename(sess_id))
        d = Debugger(code, sess_id, DebuggerTests._session_manager)
        print("setup breakpoints")
        d.set_breakpoint(4)
        self.assertEqual(d.get_breakpoints(), {4})
        print("call d.run()")
        d.run()

        #set input i0=10000000
        d.process_user_input("10000000")

        time.sleep(0.2)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        #TODO stacktrace?

        print("resume after first breakpoint")
        #TODO get stacktrace and assert

        # after this resume, the debugger should spend about 2 seconds
        # in RUNNING state
        d.resume()
        time.sleep(0.1)
        self.assertEqual(d.poll_state(), DebuggerState.RUNNING)
        self.assertEqual(d.poll_state(), DebuggerState.RUNNING)
        time.sleep(10)
        self.assertEqual(d.poll_state(), DebuggerState.NOTSTARTED)

    # Test debugging of test program loop.lw to check debugger state
    # after resume in a long enduring loop
    def test_program_loop2(self):
        print("\n== start test_program_loop2 ==")
        with open("test_programs/loop.lw", "r") as input_file:
            code = input_file.read()
        sess_id = self._next_session_id()
        d = Debugger(code, sess_id, DebuggerTests._session_manager)
        print("call d.run()")
        d.run()
        self.assertEqual(d.get_breakpoints(), set())

        # set input i0=10000000
        d.process_user_input("10000000")

        # after run, the debugger should spend about 2 seconds
        # in RUNNING state
        time.sleep(0.1)
        self.assertEqual(d.poll_state(), DebuggerState.RUNNING)
        self.assertEqual(d.poll_state(), DebuggerState.RUNNING)
        time.sleep(10)
        self.assertEqual(d.poll_state(), DebuggerState.NOTSTARTED)

    # Test debugging of test program loop.lw to check error handling
    # for set_breakpoint and remove_breakpoint
    def test_program_loop3(self):
        print("\n== start test_program_loop3 ==")
        with open("test_programs/loop.lw", "r") as input_file:
            code = input_file.read()
        sess_id = self._next_session_id()
        input_file_path = os.path.abspath(DebuggerTests._session_manager.get_input_filename(sess_id))
        d = Debugger(code, sess_id, DebuggerTests._session_manager)

        print("set breakpoints")
        self.assertEqual(d.get_breakpoints(), set())
        occurred = False
        try:
            d.set_breakpoint(2)
        except DebuggerErrorMessage as e:
            occurred = True
        self.assertTrue(occurred, "Exception has not been raised.")
        self.assertEqual(d.get_breakpoints(), set())
        occurred = False
        try:
            d.set_breakpoint(3)
        except DebuggerErrorMessage as e:
            occurred = True
        self.assertTrue(occurred, "Exception has not been raised.")
        self.assertEqual(d.get_breakpoints(), set())
        d.set_breakpoint(4)
        self.assertEqual(d.poll_state(), DebuggerState.NOTSTARTED)
        self.assertEqual(d.get_breakpoints(), {4})

        print("call d.run()")
        d.run()

        # set input i0=1
        d.process_user_input("1")

        time.sleep(0.1)
        self.assertEqual(d.poll_state(), DebuggerState.PAUSED)
        self.assertEqual(d.last_stacktrace(), [
                         {"file":input_file_path,
                          "line":4,
                          "macro":"root",
                          "bindings":[{"VarType":"input","Ident":"i0","Val":1},
                                      {"VarType":"output","Ident":"o0","Val":0}]}])
        print("set more breakpoints")
        d.set_breakpoint(5)
        d.set_breakpoint(6)
        occurred = False
        try:
            d.set_breakpoint(7)
        except DebuggerErrorMessage as e:
            occurred = True
        self.assertTrue(occurred, "Exception has not been raised.")
        self.assertEqual(d.get_breakpoints(), {4,5,6})

        # Try to set a breakpoint on illegal line numbers
        occurred = False
        try:
            d.set_breakpoint(42)
        except DebuggerErrorMessage as e:
            occurred = True
        self.assertTrue(occurred, "Exception has not been raised.")
        occurred = False
        try:
            d.set_breakpoint(-1)
        except DebuggerErrorMessage as e:
            occurred = True
        self.assertTrue(occurred, "Exception has not been raised.")
        self.assertEqual(d.get_breakpoints(), {4, 5, 6})
        
        d.step_over()
        self.assertEqual(d.last_stacktrace(), [{"file":input_file_path,
                                                "line":5,
                                                "macro":"root",
                                                "bindings":[{"VarType":"input","Ident":"i0","Val":1},
                                                            {"VarType":"output","Ident":"o0","Val":1}]}])

        # Try to clear a breakpoint where no breakpoint has been set
        # No Exeption must be thrown in this case, but the set of breakpoints
        # must also not be modified.
        d.remove_breakpoint(9)
        self.assertEqual(d.get_breakpoints(), {4, 5, 6})

        d.close()


    # Test debugging of test program multiply.lw
    def test_program_multiply(self):
        pass

if __name__ == '__main__':
    unittest.main()
