#  SessionManager.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#  
#  This module is used to manage user sessions


import threading

_running_sessions = set()
_last_session_id = 0
_lock = threading.Lock()
with _lock:
	_running_sessions.add(0) #0 is an illegal session id


#  
#  name: create_session
#  @return a new allocated session_id that is valid as long as delete_session
#  
def create_session():
	global _last_session_id
	global _running_sessions
	global _lock
	with _lock:
		nextid = _last_session_id+1;
		while str(nextid) in _running_sessions:
			if nextid == _last_session_id:
				raise RuntimeError("All session ids used");
			nextid += 1
		_last_session_id = nextid;
		_running_sessions.add(str(nextid));
		return str(nextid);


#  
#  name: check_session
#  @param sess_id session id
#  @return whether session_id is a valid session id or not
#  
def check_session(sess_id):
	with _lock:
		return sess_id in _running_sessions


#  
#  name: delete_session
#  @param sess_id session id
#  
#  Deletes the session if sess_id is valid, otherwise, a KeyError
#  will be raised
#  
def delete_session(sess_id):
	with _lock:
		_running_sessions.remove(sess_id);
