#  PortManager.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  TODO: add module description

import threading
from ListeningSocket import ListeningSocket
import Logging

_host = "127.0.0.1"
logger = Logging.get_logger(__name__)

class SocketManager:
    # Initializes the PSocketManager and assigns it the port range [first, last].
    # Note that the process must have the necessary rights to open a listening
    # socket on each of this ports.
    def __init__(self, first, last):
        self._first = first
        self._last = last
        self._ports_in_use = set()
        self._next_port_no = first
        self._lock = threading.Lock()
    
    # Returns a tuple (port, sock) with a port and a new socket listening
    # to this port
    def create_socket(self):
        with self._lock:
            while True:
                # Find port number that is not currently assigned
                port_no = self._next_port_no
                while port_no in self._ports_in_use:
                    port_no += 1
                    if port_no > self._last:
                        port_no = self._first
                    if port_no == self._next_port_no:
                        raise Exception("All possible ports are in use")
                # Check if that port is realy unused (another process
                # could possibly use that port).
                logger.debug("create_socket() - using port " + str(port_no))
                sock = ListeningSocket(_host, port_no)
                
                self._ports_in_use.add(port_no)
                self._next_port_no = port_no + 1
                if self._next_port_no > self._last:
                    self._next_port_no = self._first
                return sock
                    

    #  
    #  name: releasePort()
    #  @param listening_socket ListeningSocket object that was created by create_socket()
    #  @throws KeyError
    #  
    def release_socket(self, listening_socket):
        listening_socket.close()
        with self._lock:
            port_no = listening_socket.get_port_no()
            self._ports_in_use.remove(port_no)
