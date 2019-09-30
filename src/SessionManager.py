#  SessionManager.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#  
#  This module is used to manage user session ids


import threading

from Timer import Timer


class SessionManager:
    def __init__(self, src_path, max_sessions):
        self._running_sessions = {0} #0 is an illegal session id
        self._last_session_id = 0
        self._lock = threading.Lock()

        # maps session_ids to Session objects
        self._session_map = {}

        self._timer = Timer()
        self._timer.start()

        self._src_path = src_path
        self._max_sessions = max_sessions
    
    #  
    #  name: create_session
    #  @return a new allocated session_id that is valid as long as delete_session
    #  
    def _create_session_id(self):
        with self._lock:
            nextid = self._last_session_id+1;
            while str(nextid) in self._running_sessions:
                if nextid == self._last_session_id:
                    raise RuntimeError("All session ids used");
                nextid += 1
            self._last_session_id = nextid;
            self._running_sessions.add(str(nextid));
            return str(nextid)

    #  
    #  name: check_session
    #  @param sess_id session id
    #  @return whether session_id is a valid session id or not
    #  
    def check_session_id(self, sess_id):
        with self._lock:
            return sess_id in self._running_sessions

    #  
    #  name: delete_session
    #  @param sess_id session id
    #  
    #  Deletes the session if sess_id is valid, otherwise, a KeyError
    #  will be raised
    #  
    def _delete_session_id(self, sess_id):
        with self._lock:
            self._running_sessions.remove(sess_id);

    def get_input_filename(self, sess_id):
        return self._src_path + "/" + str(sess_id) + ".in"

    def shutdown(self):
        self._timer.close_and_flush()

    # creates a interpreter or debugger session using the factory object factory
    def create(self, factory, code):
        session_id = self._create_session_id()
        session = factory(code, session_id, self)
        timeout = session.get_timeout()
        with self._lock:
            self._session_map[session_id] = session
        self._timer.add_task(lambda : self._shutdown_session_handler(session_id), timeout)
        return session

    def _shutdown_session_handler(self, session_id):
        with self._lock:
            session = self._session_map[session_id]
            session.close()
            del self._session_map[session_id]
        

    # Returns the Session with session_id sess_id.
    # Raises KeyError, if no Session with that sess_id exists.
    def get_session(self, sess_id):
        with self._lock:
            return self._session_map[sess_id]
