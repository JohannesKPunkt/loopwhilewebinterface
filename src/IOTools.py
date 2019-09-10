#  IOTools.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#
#  This module provides some generic IO helper functions

from select import select
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
