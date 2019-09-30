#  ListeningSocket.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This class captures a socket object with the additional information
#  to which port that socket is listening to.

import socket
import Logging

logger = Logging.get_logger(__name__)

class ListeningSocket(socket.socket):
    def __init__(self, host_addr, port_no):
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        self._port_no = port_no
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            logger.debug("__init__: binding to " 
                  + str((host_addr, port_no)))
            self.bind((host_addr, port_no))
            self.listen()
        except Exception as e:
            self.close()
            raise(e)
    
    def get_port_no(self):
        return self._port_no
