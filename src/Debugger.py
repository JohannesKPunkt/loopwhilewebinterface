#  Debugger.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module encapsulates the connection to the debugger

import json
from enum import Enum
import threading
import Logging
import socket
import time

from external_libs.lexer import Lexer
from IOTools import read_timeout, LineBuffer, ConnectionClosed
from DebuggerExceptions import DebuggerErrorMessage, CompilerErrorMessage, DebuggingException
from SocketManager import SocketManager
from SessionManager import SessionManager
from Session import Session
from SourceCodeView import Tokenizer

_lexer_rules = [
    ('\d\d\d\d/\d\d/\d\d \d\d:\d\d:\d\d',                      'DATE_TIME'),
    ('\[(.)+\]#',                                              'JSON_STR'),
    ('#',                                                      'HASHTAG'),
    ('-?\d+',                                                  'INTEGER'),
    ('(\w| |\d|,)+',                                           'STR'),
]

_debugger_cmd_timeout = 15.0

class TelegramType(Enum):
    AT_BREAKPOINT = 0
    BREAKPOINT_SET = 1
    STEPPED = 2
    STACKTRACE = 3

class DebuggerTelegram:
    def __init__(self, ttype, line_no, breakpoint_no, data):
        self.ttype = ttype
        self.line_no = line_no
        self.breakpoint_no = breakpoint_no
        self.data = data

    def __str__(self):
        return str(self.ttype) + " " + str(self.line_no) + " " + str(self.breakpoint_no) + " " + str(self.data)

class DebuggerState(Enum):
    NOTSTARTED = 0
    RUNNING = 1
    PAUSED = 2
    DIED = 3

_socket_manager = SocketManager(10000, 20000)
DEBUGGER_TIMEOUT = 5*60
DEBUGGER_ACCEPT_TIMEOUT = 0.75
logger = Logging.get_logger(__name__)


class Debugger(Session):
    def __init__(self, code, sess_id, session_manager):
        super().__init__(sess_id, session_manager)
        # set of line numbers (int) on which breakpoints are set
        self._breakpoints = set()

        # _lock is now provided by superclass session
        #self._lock = threading.Lock() 

        self._last_state = DebuggerState.NOTSTARTED
        self._last_stacktrace = None

        # socket to listen for debugger process
        self._socket = _socket_manager.create_socket()
        self._socket.settimeout(DEBUGGER_ACCEPT_TIMEOUT)

        # debugger process self._proc
        self._create_process(code, True, self._socket.get_port_no())

        # source file containing the users code
        self._input_file_name = self._sess_man.get_input_filename(sess_id)

        # if debugger is started via "start" command, execution is halted
        # at the first line of the root macro, so we need a temporary breakpoint
        # that will be deleted as soon as execution reaches the first line
        self._start_line = -1

        # connection to the debugger process
        self._conn = None
        try:
            self._conn, _ = self._socket.accept()
        except socket.timeout:
            # timeout happens normally in case of syntax errors, where
            # the interpreter process terminates immediately
            return

        self._line_buffer = LineBuffer(self._conn)

    def _restart(self):
        with self._lock:
            self._conn.close()
            self._conn = None
            self._proc.kill()
            # wait to remove zombies
            self._proc.wait(5)

            self._last_stacktrace = None

            self._create_process(None, True, self._socket.get_port_no(), reuse_input_file=True)
            self._last_state = DebuggerState.NOTSTARTED
            try:
                self._conn, _ = self._socket.accept()
            except socket.timeout:
                return
            self._line_buffer = LineBuffer(self._conn)

            # transfer all breakpoints to new debugger process
            old_breakpoints = self._breakpoints
            self._breakpoints = set()
            for bp in old_breakpoints:
                self.set_breakpoint(bp)

    # returns True, if the debugger process failed, e.g. in case of a syntax error
    # in the given program
    def is_failed(self):
        return self._conn is None

    def get_status(self):
        with self._lock:
            if self._proc != None:
                return "running"
            else:
                return "terminated"

    def get_proc(self):
        return self._proc

    def close(self):
        self.kill()

    def kill(self):
        with self._lock:
            if self._proc is not None:
                self._socket.close()
                try:
                    self._conn.close()
                except:
                    # in case of syntax errors, the debugger process terminates
                    # right after termination, so no connection exists.
                    pass
                self._kill()

    # Returns a set with the line numbers of all set breakpoints
    def get_breakpoints(self):
        return self._breakpoints

    # sends a command to the debugger process
    def _send_cmd(self, cmd):
        logger.debug("_send_cmd(): sending command \"" + cmd + "\" to debugger process.")
        to_write = (cmd + "\n").encode()
        self._conn.send(to_write)
        #self._conn.flush()

    # waits for a response and returns parsed response object
    # returns None if no response is available
    def _poll_response(self):
        response = self._line_buffer.poll_line()
        if response is not None:
            return self.parse_debugger_output(response)
        return None

    # Reads all debugger telegrams from the debugger and processes them.
    # This method will not block, so after a call, there might be new
    # unprocessed telegrams.
    # Additionally, one can specify a several type of Telegram in parameter
    # ttype, such that the least processed telegram of that type will be returned.
    def _process_telegrams(self, ttype=None):
        last_tgram = None
        while True:
            try:
                response = self._poll_response()
                if response is None:
                    break
            except ConnectionClosed:
                self._restart()
                return last_tgram

            # update type
            if response.ttype in [TelegramType.AT_BREAKPOINT, TelegramType.STEPPED]:
                self._last_state = DebuggerState.PAUSED

            # update stacktrace
            if response.data is not None:
                self._last_stacktrace = response.data
            
            if ttype is response.ttype:
                last_tgram = response
        if self._last_state == DebuggerState.PAUSED and self._start_line > -1:
            self.remove_breakpoint(self._start_line)
        return last_tgram

    # waits for a response of a certain TelegramType, or an
    # possible Exception
    def _wait_for_debugger_response(self, ttype):
        last_tgram = None
        i = 0
        while last_tgram is None and i < 10:
            last_tgram = self._process_telegrams(ttype)
            i += 1
            if i == 9:
                time.sleep(0.1)
        return last_tgram
        

    # returns the current state of the debugger
    def poll_state(self):
        self._process_telegrams()
        return self._last_state

    # returns last received stacktrace
    def last_stacktrace(self):
        self._process_telegrams()
        return self._last_stacktrace

    # returns last received stacktrace and resets it to None
    def pop_last_stacktrace(self):
        self._process_telegrams()
        st = self._last_stacktrace
        self._last_stacktrace = None
        return st

    # Fails with an DebuggerErrorMessage Exception, if line_no is not valid
    def set_breakpoint(self, line_no):
        self._send_cmd("setbreakpoint " +  str(line_no) + " " + self._input_file_name)
        resp = self._wait_for_debugger_response(TelegramType.BREAKPOINT_SET)
        #logger.debug("line_no=" + str(line_no) + " type=" + str(type(line_no)) + ", resp.line_np=" + str(resp.line_no) + ", type=" + str(type(resp.line_no)))
        assert(line_no == resp.line_no)
        self._breakpoints.add(line_no)

    # In case line_no is not valid, NO Exception is thrown.
    def remove_breakpoint(self, line_no):
        if line_no in self._breakpoints:
            self._send_cmd("clearbreakpoint " + str(line_no) + " " + self._input_file_name)
            self._breakpoints.remove(line_no)

    def step_over(self):
        if self._last_state not in [DebuggerState.DIED, DebuggerState.NOTSTARTED]:
            self._last_state = DebuggerState.RUNNING
            self._send_cmd("stepover")

    def step_into(self):
        if self._last_state not in [DebuggerState.DIED, DebuggerState.NOTSTARTED]:
            self._last_state = DebuggerState.RUNNING
            self._send_cmd("stepinto")

    def step_out(self):
        if self._last_state not in [DebuggerState.DIED, DebuggerState.NOTSTARTED]:
            self._last_state = DebuggerState.RUNNING
            self._send_cmd("stepout")

    def resume(self):
        if self._last_state not in [DebuggerState.DIED, DebuggerState.NOTSTARTED]:
            self._last_state = DebuggerState.RUNNING
            self._send_cmd("resume")

    def run(self):
        if self._last_state is DebuggerState.NOTSTARTED:
            self._last_state = DebuggerState.RUNNING
            self._send_cmd("run")

    class StatefulTokenizer:
        def __init__(self, source):
            self._lexer = Tokenizer(source).__iter__()
            self._line = 1
            self._token = None
            self.consume_token()

        def cur_line(self):
            return self._line

        def has_token(self):
            return self._token is not None

        def consume_token(self):
            cur_token = self._token
            if self._token is not None and self._token.type == "LINEBREAK":
                print("inc line")
                self._line += 1
            try:
                self._token = self._lexer.__next__()
            except:
                self._token = None
            return cur_token

        def skip_whitespaces(self):
            while self._token.type in ("SPACE", "TAB", "LINEBREAK"):
                self.consume_token()

        def consume_non_whitespace_token(self):
            self.skip_whitespaces()
            return self.consume_token()

        def consume_until_value(self, value):
            while self.has_token():
                if self._token.val == value:
                    return
                self.consume_token()

        def consume_until(self, ttype):
            while self.has_token():
                if self._token.type == ttype:
                    return
                self.consume_token()

        def peek_token(self):
            return self._token

    def run_and_stop_at_first_line(self):
        # determine first line of root macro
        source = self.get_program_code()
        tokenizer = self.StatefulTokenizer(source)

        while tokenizer.has_token():
            token = tokenizer.consume_non_whitespace_token()
            print(token)
            if token.type == "ENTER_COMMENT":
                tokenizer.consume_until("LINEBREAK")
            if token.val == "def":
                tokenizer.consume_until_value("enddef")
            elif token.val in ("in", "out", "aux"):
                print("handle param decl")
                print(tokenizer.consume_non_whitespace_token()) # colon
                print(tokenizer.consume_non_whitespace_token()) # first parameter
                while tokenizer.peek_token().val == ",":
                    tokenizer.consume_non_whitespace_token() # comma
                    tokenizer.consume_non_whitespace_token() # next parameter
            #elif token.type in ("SPACE", "TAB", "COLON", "SEMICOLON", "LP", "RP"
            elif token.type == "IDENTIFIER":
                break

        # set a temporary breakpoint
        self._start_line = tokenizer.cur_line()
        self.set_breakpoint(self._start_line)

        # run
        self.run()

    @staticmethod
    def parse_debugger_output(debugger_output):
        lexer = Lexer(_lexer_rules, True)
        lexer.input(debugger_output)
        token = lexer.token()
        if token.type == 'DATE_TIME':
            #TODO this is an compiler error message
            raise CompilerErrorMessage(debugger_output)
        elif token.type == 'INTEGER':
            type_no = int(token.val);
            ttype = TelegramType(type_no)

            token = lexer.token()
            if token.type != 'INTEGER':
                raise DebuggingException("Unexpected token of type " + token.type +" (INTEGER expected) at pos: "
                                         + token.pos + " in debugger response. "
                                         + "Entire response is: " + debugger_output)
            line_no = int(token.val)

            token = lexer.token()
            if token.type != 'INTEGER':
                raise DebuggingException("Unexpected token of type " + token.type +" (INTEGER expected) at pos: "
                                         + token.pos + " in debugger response. "
                                         + "Entire response is: " + debugger_output)
            breakpoint_no = int(token.val)
            
            
            token = lexer.token()
            if token.type == 'JSON_STR':
                #parse json
                json_str = token.val[:len(token.val)-1]
                data = json.loads(json_str)
            else:
                data = None
            return DebuggerTelegram(ttype, line_no, breakpoint_no, data)
        elif token.type == 'STR':
            raise DebuggerErrorMessage(token.val)
        else:
            raise DebuggingException("Unexpected token of type " + token.type +" (DATE_TIME, INTEGER or STR expected) at pos: "
                                     + token.pos + " in debugger response. "
                                     + "Entire response is: " + debugger_output)
    
    @staticmethod
    def get_timeout():
        return DEBUGGER_TIMEOUT
