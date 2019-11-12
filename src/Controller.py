#  Controller.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#
#

from tg import TGController, expose
import traceback

from SessionManager import SessionManager
from IOTools import read_timeout
from DebuggerView import DebuggerView
from Debugger import Debugger, DebuggerState
from InterpreterView import InterpreterView
from Interpreter import Interpreter
import Logging

# String constants
SESSION_ID = "session_id"
PROGRAM_CODE = "program_code"
ACTION = "action"

logger = Logging.get_logger(__name__)

class Controller(TGController):
    def __init__(self, src_path, max_sessions):
        super().__init__()
        self._sess_man = SessionManager(src_path, max_sessions)

    def shutdown(self):
        self._sess_man.shutdown()


	# this function is implementing the /run side, that receives the program the user wants to execute
	# and returns a unique session id
    @expose(content_type="text/plain")
    def run(self, **kw):
        try:
            logger.debug("run() called")
            program_code = kw[PROGRAM_CODE]
            session = self._sess_man.create(Interpreter, program_code)
            logger.debug("run(): new session_id=" + str(session.get_id()))
            return str(session.get_id());
        except Exception as e:
            logger.error("run(): The following exception occurred: " + traceback.format_exc())
            return "0"
    
    # /stop is used to kill the interpreter process by user clicking the stop button
    @expose(content_type="text/plain")
    def stop(self, **kw):
        session_id = None
        try:
            session_id = kw[SESSION_ID]
            logger.debug("stop() called, session_id=" + str(session_id))
            session = self._sess_man.get_session(kw[SESSION_ID])
            session.stop()
            return "OK"
        except KeyError as e:
            logger.info("stop(): Invalid session_id=" + str(session_id))
            return "An error occurred: invalid session (id=" + str(session_id) + ")."
        except Exception as e:
            logger.error("stop(): The following exception occurred: " + traceback.format_exc())
            return "An unexpected server-sided exception occurred."
    
    # /shell receives a command line the user entered in the shell and returns a response string
    @expose(content_type="text/plain")
    def shell(self, **kw):
        try:
            shell_input = kw["input"]
            session_id = kw[SESSION_ID]
            logger.debug("shell() called, session_id=" + str(session_id) + ", input=" + shell_input)
            session = self._sess_man.get_session(session_id)
            # If the user sends empty string as input, he just wants
            # to poll the interpreter output
            if shell_input != "":
                session.process_user_input(shell_input)

            return session.poll_user_output()
        except KeyError as e:
            logger.info("shell(): KeyError:" + str(e))
            return "An error occurred."
        except Exception as e:
            logger.error("shell(): Exception when write/read to child process: " + traceback.format_exc())
            return "An error occurred."
    
    # returns either "running", "terminated", "timeout" or "error"
    @expose(content_type="text/plain")
    def check_termination(self, **kw):
        try:
            session_id = kw[SESSION_ID]
            logger.debug("check_termination() called, session_id=" + str(session_id))
            session = self._sess_man.get_session(session_id)
            return session.get_status()
        except KeyError as e:
            logger.info("check_termination(): KeyError (invalid session id):" + str(e))
            return "timeout"
        except Exception as e:
            logger.error("check_termination(): Exception:" + str(e))
            return "error"

    @expose(content_type="text")
    def set_breakpoint(self, **kw):
        try:
            line_no = kw["line_no"]
            session_id = kw[SESSION_ID]
            logger.debug("set_breakpoint() called, session_id=" + str(session_id) + ", line=" + str(line_no))
            session = self._sess_man.get_session(session_id)
            session.set_breakpoint(int(line_no))
            return "OK"
        except Exception as e:
            logger.error("set_breakpoint(): Exception: " + traceback.format_exc())
            return "FAIL"

    @expose(content_type="text")
    def remove_breakpoint(self, **kw):
        try:
            line_no = kw["line_no"]
            session_id = kw[SESSION_ID]
            logger.debug("remove_breakpoint() called, session_id=" + str(session_id) + ", line=" + str(line_no))
            session = self._sess_man.get_session(session_id)
            session.remove_breakpoint(int(line_no))
        except KeyError as e:
            logger.info("remove_breakpoint(): KeyError (invalid session id):" + str(e))
        except Exception as e:
            logger.error("remove_breakpoint(): Exception: " + traceback.format_exc())

    @expose(content_type="text")
    def debugger_poll_state(self, **kw):
        try:
            session_id = kw[SESSION_ID]
            logger.debug("debugger_poll_state() called, session_id=" + 
                         str(session_id))
            session = self._sess_man.get_session(session_id)
            state = session.poll_state()
            if state is DebuggerState.DIED:
                return "DIED"
            elif state is DebuggerState.NOTSTARTED:
                return "RESTARTED"
            else:
                #return "line" + str(session.last_stacktrace()[0]["line"])
                st = str(session.pop_last_stacktrace()).replace("\'", "\"")
                logger.debug(st)
                return st
        except KeyError as e:
            logger.info("debugger_poll_state(): KeyError (invalid session id):" + str(e))
        except:
            logger.error("debugger_poll_state(): Exception:" + traceback.format_exc())
        return "FAIL"

    @expose(content_type="text")
    def debugger_action(self, **kw):
        try:
            session_id = kw[SESSION_ID]
            action = kw[ACTION]
            logger.debug("debugger_action() called, session_id=" + 
                         str(session_id) + ", action=" + str(action))
            session = self._sess_man.get_session(session_id)
            if action == "continue":
                state = session.poll_state()
                if state is DebuggerState.NOTSTARTED:
                    logger.debug("debugger_action(): calling session.run()")
                    session.run()
                else:
                    logger.debug("debugger_action(): calling session.resume()")
                    session.resume()
            elif action == "stepinto":
                session.step_into()
            elif action == "stepout":
                session.step_out()
            elif action == "stepover":
                session.step_over()
            elif action == "close":
                session.close()
            else:
                return "FAIL"
            return "OK"
        except:
            logger.error("debugger_action(): Exception:" + traceback.format_exc())
            return "FAIL"

    # /debugger is the main side of the debugger mode
    #@expose()#(content_type="text/html")
    @expose('templates/interpreter.xhtml', content_type="text/html")
    def debugger(self, **kw):
        logger.debug("debugger() called")
        program_code = kw[PROGRAM_CODE]
        session = self._sess_man.create(Debugger, program_code)
        logger.debug("debugger(): new session_id=" + str(session.get_id()))
        return DebuggerView(program_code, session.get_id())


    # /interpreter is the main site of the interpreter mode
    @expose('templates/interpreter.xhtml', content_type="text/html")
    def interpreter(self, **kw):
        try:
            program_code = kw[PROGRAM_CODE]
        except:
            program_code = None
        return InterpreterView(program_code)
