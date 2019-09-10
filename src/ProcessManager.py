#  ProcessManager.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#  
#  This module is used to manage spawned child processes (instances
#  of the lwre interpreter/debugger)


import subprocess
import threading
import os

from SessionManager import delete_session


_executable_path = "./lwre"
_timeout_period = 30.0
_max_procs_limit = 15
_src_path = "./user_src"
_zombie_period = 5*60.0

_running_procs = {}
_lock = threading.Lock()

def _get_input_filename(sess_id):
    return _src_path + "/" + str(sess_id) + ".in"

# creates a instance of the interpreter and returns the corresponding
# Popen object
def create_process(sess_id, input_data, debug=False):
    with _lock:
        if len(_running_procs) > _max_procs_limit:
            raise RuntimeError("To many processes running")
    
    input_file_path = _get_input_filename(sess_id)
    try:
        with open(input_file_path, "x") as input_file:
            input_file.write(input_data)
    except FileExistsError as e:
        raise RuntimeError("Input file for session_id " + str(sess_id) + " already exists: " + str(e))
    
    if debug:
        callstr = [_executable_path, "-d", input_file_path, "-port", "0"]
    else:
        callstr = [_executable_path, input_file_path]
    print("create_process(): creating process of session " + str(sess_id))
    try:
        proc = subprocess.Popen(callstr, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("create_process(): process with PID=" + str(proc.pid) + " created.")
    except Exception as e:
        try:
            print("try remove")
            os.remove(_get_input_filename(sess_id))
        except Exception as ex:
            print("create_process(): create_process: remove of input file after failed spawning also failed: " + str(ex))
        raise RuntimeError("Could not spawn child process: " + e)
    
    with _lock:
        _running_procs[sess_id] = proc
    
    # Timer to kill spawned process after _timeout_period has elapsed
    threading.Timer(_timeout_period, lambda : kill_process(sess_id)).start()
    
    return proc

def get_process(sess_id):
    with _lock:
        return _running_procs[sess_id]


def get_process_status(sess_id):
    with _lock:
        try:
            proc = _running_procs[sess_id]
            if proc.poll() is None:
                return "running"
            elif proc.returncode < 0:
                return "timeout"
            else:
                return "terminated"
        except Exception as e:
            return "error"

def remove_process_data(sess_id):
    with _lock:
        del _running_procs[sess_id]
        delete_session(sess_id)

def kill_process(sess_id):
    print("killing process of session " + str(sess_id))
    try:
        with _lock:
            proc = _running_procs[sess_id]
            #give the user another 5 minutes to recognize that the programm timed out
            threading.Timer(_zombie_period, lambda : remove_process_data(sess_id)).start()
    except Exception as e:
        print("kill_process(): failed with an exception. Maybe stop was called by user before.")
        print(e)
        proc = None

    try:
        proc.kill()
        # wait to remove zombies
        proc.wait(5)
    except Exception as e:
        print("kill_process(): kill failed: " + str(e))
    
    try:
        os.remove(_get_input_filename(sess_id))
    except Exception as e:
        print("kill_process(): removing input file of session " + str(sess_id) + " failed: " + str(e))
