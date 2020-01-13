#  WebSockets.py
#
#  Copyright 2020 Johannes Kern <johannes.kern@fau.de>
#
#
#  This module provides a WebSocket-based protocol for updating
#  the view of a Interpreter or Debugger session without polling

import Logging
from Debugger import Debugger, DebuggerState

from threading import Thread, Lock
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet import reactor
from twisted.python import log
from queue import Queue
from select import select
import sys
import json
import traceback


SELECT_TIMEOUT = 0.10
_logger = Logging.get_logger(__name__)
_observer = None

class WebSocketsService(Thread):
    def __init__(self, sess_man, host, interface, port):
        global _observer
        super().__init__()
        self.host = host
        self.port = port
        self.interface = interface
        _observer = self.Observer(sess_man)

    def run(self):
        try:
            log.PythonLoggingObserver(__name__).start()

            factory = WebSocketServerFactory("ws://" + self.host + ":" + str(self.port))
            factory.protocol = LoopWhileWSConnection

            _observer.start()

            reactor.listenTCP(self.port, factory, interface=self.interface)
            reactor.run(installSignalHandlers=False)
        finally:
            _logger.info("stop Observer")
            _observer.stop()

    def stop(self):
        reactor.callFromThread(reactor.stop)

    # Thread that observes connections of active sessions for
    # events to process.
    # It administrates a set of file descriptors that are passively
    # observed by the UNIX select call. In case of an event, an update
    # message for the client connection is generated. This update message
    # contains informations about state changes of the session object that
    # are historically obtained by polling /poll_debugger_state, /shell etc.
    class Observer(Thread):
        def __init__(self, sess_man):
            super().__init__()
            self._sess_man = sess_man
            self.stopped = False
            self._lock = Lock()

            # set of file descriptors
            self._select_set = set()

            # maps file descriptors to owning sessions
            self._conn_map = {}

        def add_connection(self, conn):
            try:
                session = self._sess_man.get_session(conn.session_id)
                fds = session.get_file_descriptors()
                conn.fds = fds
                with(self._lock):
                    for fd in fds:
                        self._select_set.add(fd)
                        self._conn_map[fd] = conn
            except Exception:
                conn.close()
                _logger.error(traceback.format_exc())

        def remove_connection(self, conn):
            try:
                with(self._lock):
                    for fd in conn.fds:
                        self._select_set.remove(fd)
                        self._conn_map.pop(fd)
            except Exception:
                _logger.error(traceback.format_exc())

        def _handle_event(self, fd):
            try:
                conn = self._conn_map[fd]
            except KeyError:
                _logger.warn(traceback.format_exc())
                return

            try:
                session = self._sess_man.get_session(conn.session_id)

                response = {"status":   session.get_status(),
                            "terminal": session.fast_poll_user_output(),
                            "debugger": ""
                           }
                if isinstance(session, Debugger):
                    state = session.poll_state()
                    if state is DebuggerState.DIED:
                        response["debugger"] = "DIED"
                    elif state is DebuggerState.NOTSTARTED:
                        response["debugger"] = "RESTARTED"
                    else:
                        response["debugger"] = str(session.pop_last_stacktrace()).replace("\'", "\"")
                message = json.dumps(response)
                if message != conn.last_msg:
                    conn.sendMessage(message.encode("UTF8"), False)
                    if response["status"] != "running" or response["debugger"] == "RESTARTED":
                        conn.close()
                        self.remove_connection(conn)
                        return
                conn.last_msg = message

            except KeyError:
                # session is closed or invalid
                conn.sendMessage("{\"status\": \"timeout\", \"terminal\": \"\", \"debugger\": \"DIED\"}".encode("UTF8"), False)
                conn.close()
                self.remove_connection(conn)
            except Exception:
                _logger.error(traceback.format_exc())

        def run(self):
            while(True):
                if self.stopped:
                    return
                try:
                    with self._lock:
                        fds = list(self._select_set)
                    result = select(fds, [], fds, SELECT_TIMEOUT)

                    # fds ready to read
                    for fd in result[0]:
                        self._handle_event(fd)

                    # fds with an "exceptional condition"
                    for fd in result[2]:
                        self._handle_event(fd)
                except OSError:
                    # Bad file descriptor in self._select_set
                    self._repair()
                except Exception:
                    _logger.error(traceback.format_exc())

        def _repair(self):
            _logger.debug("_repair(): begin")
            with self._lock:
                self._select_set = set()
                connections = self._conn_map.values()
                self._conn_map = {}
                for conn in connections:
                    try:
                        session = self._sess_man.get_session(conn.session_id)
                        fds = session.get_file_descriptors()
                        conn.fds = fds
                        for fd in fds:
                            self._select_set.add(fd)
                            self._conn_map[fd] = conn
                    except KeyError:
                        _logger.debug("_repair(): invalid session: " + str(conn.session_id))
                    except Exception:
                        _logger.info(traceback.format_exc())
                        try:
                            conn.close()
                        except Exception:
                            _logger.debug(traceback.format_exc())

            _logger.debug("_repair() finished")

        def stop(self):
            self.stopped = True


class LoopWhileWSConnection(WebSocketServerProtocol):
    def __init__(self):
        super().__init__()
        self.session_id = None
        self.last_msg = ""
        self.fds = None
        self.closed = False

    def onMessage(self, payload, isBinary):
        if self.session_id is not None:
            self.sendClose()
        else:
            self.session_id = payload.decode()
            _observer.add_connection(self)

    def close(self):
        if not self.closed:
            self.closed = True
            self.sendClose()

    def onClose(self, wasClean, code, reason):
        _logger.debug("Connection (session_id=" + str(self.session_id) + ") closed: " + str(reason))
        try:
            if not self.closed:
                _observer.remove_connection(self)
        except Exception:
            _logger.debug(traceback.format_exc())
