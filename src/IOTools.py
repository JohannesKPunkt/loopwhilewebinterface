#  IOTools.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module provides some generic IO helper functions

from select import select
import socket
import os


#  
#  name: read_timeout
#  @param
#    stream stream from which we want to read
#    timeout timeout in seconds
#  @return string
#  
def read_timeout(stream, timeout):
    r1, r2, r3 = select([stream], [], [stream], timeout)
    result = "".encode()
    if stream in r1 + r2 + r3:
        fileno = stream.fileno()
        result += os.read(fileno, 512)
    
    return result.decode()

class ConnectionClosed(Exception):
    def __init__(self):
        super().__init__("Try to read from a closed connection.")

# NOTE: using this methods is unsafe in the sence that the methods
# will read possibly infinitly many bytes from the sender
class LineBuffer:
    def __init__(self, stream, delimiter = "\n"):
        self._line_buffer = ""
        self.DELIMITER = delimiter
        self._conn = stream
        self._conn.setblocking(0)
        self._closed = False

    # Polls the underlying stream for a entire line, ended by delimiter.
    # Returns the line without the delimiter or None if no entire 
    # line is available.
    def poll_line(self):
        nl_pos = self._line_buffer.find(self.DELIMITER)
        while not self._closed:
            try:
                response = self._conn.recv(1024).decode()
                self._line_buffer += response
                nl_pos = self._line_buffer.find(self.DELIMITER)
                if response == "":
                    # connection has been closed
                    self._closed = True
                    break
            except socket.error:
                break
        if nl_pos != -1:
            first_line = self._line_buffer[:nl_pos]
            self._line_buffer = self._line_buffer[nl_pos+len(self.DELIMITER):]
            return first_line
        elif self._closed:
            raise ConnectionClosed()
        return None
