#  SessionManagerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
sys.path.append("..")
from SessionManager import create_session, check_session, delete_session

class SessionManagerTests(unittest.TestCase):
    def test_create_check_delete(self):
        sess_0 = create_session()
        sess_1 = create_session()
        self.assertTrue(check_session(sess_0))
        self.assertTrue(check_session(sess_1))
        delete_session(sess_0)
        self.assertTrue(check_session(sess_1))
        self.assertFalse(check_session(sess_0))
        delete_session(sess_1)
        self.assertFalse(check_session(sess_1))
        self.assertFalse(check_session(sess_0))
        
    def test_delete_exceptions(self):
        passed = False
        try:
            delete_session("1245241425215214");
        except KeyError:
            passed = True
        except Exception:
            passed = False
        self.assertTrue(passed)

if __name__ == '__main__':
    unittest.main()
