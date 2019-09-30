#  SocketManagerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
import tests_common
from SocketManager import SocketManager

class SocketManagerTests(unittest.TestCase):
    def test_getters(self):
        m = SocketManager(9995, 9997)

        s1 = m.create_socket()
        s2 = m.create_socket()
        s3 = m.create_socket()

        self.assertNotEqual(s1.get_port_no(), s2.get_port_no())
        self.assertNotEqual(s2.get_port_no(), s3.get_port_no())
        self.assertNotEqual(s1.get_port_no(), s3.get_port_no())

        self.assertTrue(s1.get_port_no() in [9995, 9996, 9997])
        self.assertTrue(s2.get_port_no() in [9995, 9996, 9997])
        self.assertTrue(s3.get_port_no() in [9995, 9996, 9997])

        # Try to provoke some overrun in the cyclic search of free port number
        port_no = s2.get_port_no()
        m.release_socket(s2)
        s2 = m.create_socket()
        self.assertEqual(port_no, s2.get_port_no())

        port_no = s1.get_port_no()
        m.release_socket(s1)
        s1 = m.create_socket()
        self.assertEqual(port_no, s1.get_port_no())

        # Try to create a fourth socket when no more port number is free
        occurred = False
        try:
            m.create_socket()
        except Exception as e:
            occurred = True
        self.assertTrue(occurred)
        
        m.release_socket(s1)
        m.release_socket(s2)
        m.release_socket(s3)

if __name__ == '__main__':
    unittest.main()
