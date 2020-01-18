#  Session.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#  
#  This module is used to manage spawned child processes (instances
#  of the lwre interpreter/debugger)

import Logging
import threading
import os, subprocess
import fcntl

from IOTools import read_timeout

logger = Logging.get_logger(__name__)

_executable_path = "./lwre"

#  
#  Abstract class Session.
#  Each subclass shall provide a constructor
#  __init__(code, session_id, session_manager)
#  where code is a string with the users code, session_id is the session_id
#  for this session and session_manager is the SessionManager to be used.
#  
#  Further, a method close() has to be provided which is automatically
#  called by the SessionManager, when the Session has timed out. Its purpose
#  is to perform a proper cleanup of the Sessions resources, i.e. to kill
#  the underlying interpreter process, close connections and so on.
#  
#  For the WebSockets-based communication, a method get_file_descriptors()
#  must be implemented, that returns a list of UNIX file descriptors to
#  wait on (via select()) for events on that session.
class Session:
    def __init__(self, sess_id, sess_manager, client_addr):
        self._lock = threading.Lock()
        self._sess_id = sess_id
        self._sess_man = sess_manager
        self._proc = None
        self._client_addr = client_addr
        self.timer_task = None

    def get_client_addr(self):
        return self._client_addr

    def get_id(self):
        return self._sess_id

    def process_user_input(self, input_str):
        self._proc.stdin.write((input_str + "\n").encode())
        self._proc.stdin.flush()

    # poll process output with blocking only a short period of time
    def poll_user_output(self):
        return read_timeout(self._proc.stdout, timeout=0.15)

    # poll process output without blocking at all
    def fast_poll_user_output(self):
        try:
            return os.read(self._proc.stdout.fileno(), 512).decode()
        except BlockingIOError:
            return ""

    def get_program_code(self):
        input_file_path = self._sess_man.get_input_filename(self._sess_id)
        try:
            with open(input_file_path, "r") as input_file:
                return input_file.read()
        except FileNotFoundError as e:
            raise RuntimeError("Input file for session_id " + str(self._sess_id) + " not found: " + str(e))


    # creates a instance of the interpreter process and returns the 
    # corresponding Popen object
    def _create_process(self, input_data, debug=False, debug_port=-1, reuse_input_file=False):
        input_file_path = self._sess_man.get_input_filename(self._sess_id)
        if not reuse_input_file:
            if "#IMPORT" in input_data:
                raise RuntimeError("Input program contains '#IMPORT' statement.")
            try:
                with open(input_file_path, "x") as input_file:
                    input_file.write(input_data)
            except FileExistsError as e:
                raise RuntimeError("Input file for session_id " + str(self._sess_id) + " already exists: " + str(e))

        if debug:
            callstr = [_executable_path, "-d", "-port", str(debug_port), input_file_path]
        else:
            callstr = [_executable_path, input_file_path]
        logger.debug("create_process(): creating process of session " + str(self._sess_id))
        try:
            logger.debug("create_process(): creating process with cmdline: " + str(callstr))
            self._proc = subprocess.Popen(callstr, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            logger.debug("create_process(): process with PID=" + str(self._proc.pid) + " created.")

            # use non-blocking IO for process output
            flags = fcntl.fcntl(self._proc.stdout.fileno(), fcntl.F_GETFL)
            fcntl.fcntl(self._proc.stdout.fileno(), fcntl.F_SETFL, flags | os.O_NONBLOCK)
        except Exception as e:
            try:
                os.remove(input_file_path)
            except Exception as ex:
                logger.error("create_process(): create_process: remove of input file after failed spawning also failed: " + str(ex))
            raise RuntimeError("Could not spawn child process: " + str(e))

    def _kill(self):
        logger.debug("killing process of session " + str(self._sess_id))
        try:
            self._proc.kill()
            # wait to remove zombies
            self._proc.wait(5)
            self._proc = None
        except Exception as e:
            logger.error("kill_process(): kill failed: " + str(e))
        try:
            os.remove(self._sess_man.get_input_filename(self._sess_id))
        except Exception as e:
            logger.error("kill_process(): removing input file of session " + str(self._sess_id) + " failed: " + str(e))
