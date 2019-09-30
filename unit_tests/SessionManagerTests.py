#  SessionManagerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import tests_common
import sys, unittest
from SessionManager import SessionManager

class SessionManagerTests(unittest.TestCase):
    def test_create_check_delete(self):
        sess_man = SessionManager("/dev/null", 20)
        sess_0 = sess_man._create_session_id()
        sess_1 = sess_man._create_session_id()
        self.assertTrue(sess_man.check_session_id(sess_0))
        self.assertTrue(sess_man.check_session_id(sess_1))
        sess_man._delete_session_id(sess_0)
        self.assertTrue(sess_man.check_session_id(sess_1))
        self.assertFalse(sess_man.check_session_id(sess_0))
        sess_man._delete_session_id(sess_1)
        self.assertFalse(sess_man.check_session_id(sess_1))
        self.assertFalse(sess_man.check_session_id(sess_0))
        sess_man.shutdown();
    def test_delete_exceptions(self):
        sess_man = SessionManager("/dev/null", 20)
        passed = False
        try:
            sess_man._delete_session_id("1245241425215214");
        except KeyError:
            passed = True
        except Exception:
            passed = False
        self.assertTrue(passed)
        sess_man.shutdown();

        sess_man = SessionManager("/dev/null", 20)
        sess_id = sess_man._create_session_id()
        passed = False
        try:
            sess_man._delete_session_id(sess_id + "foo");
        except KeyError:
            passed = True
        except Exception:
            passed = False
        self.assertTrue(passed)
        sess_man.shutdown();

if __name__ == '__main__':
    unittest.main()
