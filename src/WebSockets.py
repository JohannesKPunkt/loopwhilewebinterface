#  WebSockets.py
#
#  Copyright 2020 Johannes Kern <johannes.kern@fau.de>
#
#
#  This module provides a WebSocket-based protocol for updating
#  the view of a Interpreter or Debugger session without polling

import Logging
from Debugger import Debugger, DebuggerState

from threading import Thread
from autobahn.twisted.websocket import WebSocketServerProtocol
from autobahn.twisted.websocket import WebSocketServerFactory
from twisted.internet import reactor
from twisted.python import log
from queue import Queue
import sys
import json
import traceback


_queue = Queue()
_logger = Logging.get_logger(__name__)

class WebSocketsService(Thread):
    def __init__(self, sess_man, host, interface, port):
        super().__init__()
        self.host = host
        self.port = port
        self.interface = interface
        self._runner = self.QueueRunner(sess_man)

    def run(self):
        try:
            log.PythonLoggingObserver(__name__).start()

            factory = WebSocketServerFactory("ws://" + self.host + ":" + str(self.port))
            factory.protocol = LoopWhileWSConnection

            self._runner.start()

            reactor.listenTCP(self.port, factory, interface=self.interface)
            reactor.run(installSignalHandlers=False)
        finally:
            _logger.info("stop QueueRunner")
            self._runner.stop()

    def stop(self):
        reactor.callFromThread(reactor.stop)

    class QueueRunner(Thread):
        def __init__(self, sess_man):
            super().__init__()
            self._sess_man = sess_man
            self.stopped = False

        def run(self):
            while(True):
                try:
                    task = _queue.get()
                    if task is None:
                        return
                    session = self._sess_man.get_session(task.session_id)

                    response = {"status":   session.get_status(),
                                "terminal": session.poll_user_output(),
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
                    if message != task.last_msg:
                        task.sendMessage(message.encode("UTF8"), False)
                        if response["status"] != "running" or response["debugger"] == "RESTARTED":
                            task.sendClose()
                            continue
                    task.last_msg = message

                    if not self.stopped:
                        _queue.put(task)
                except KeyError:
                    # session is closed or invalid
                    task.sendMessage("{\"status\": \"timeout\", \"terminal\": \"\", \"debugger\": \"DIED\"}".encode("UTF8"), False)
                    task.sendClose()
                except Exception:
                    _logger.error(traceback.format_exc())

        def stop(self):
            self.stopped = True
            _queue.put(None)


class LoopWhileWSConnection(WebSocketServerProtocol):
    def __init__(self):
        super().__init__()
        self.session_id = None
        self.last_msg = ""

    def onMessage(self, payload, isBinary):
        if self.session_id is not None:
            self.sendClose()
        else:
            self.session_id = payload.decode()
            _queue.put(self)
