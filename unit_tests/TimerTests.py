#  TimerTests.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#

import sys, unittest
import tests_common
from Timer import *
import time

class TimerTests(unittest.TestCase):
    class Counter:
        def __init__(self):
            self._counter = 0
        def add(self, value):
            print("self._counter += " + str(value))
            self._counter += value
        def multiply(self, value):
            print("self._counter *= " + str(value))
            self._counter *= value
        def get(self):
            return self._counter

    @staticmethod
    def throw_something():
        raise Exception("This is just a test.")

    def setUp(self):
        print("== setup TimerTests ==")
        self.t = Timer()

    def tearDown(self):
        print("== teardown timerTests ==")
        try:
            self.t._lock.acquire(timeout=2)
            self.t._queue.append(Timer.Task(Timer.PoisonPill.take_it, 0))
            self.t._cond.notify()
            self.t._lock.release()
        except Exception as e:
            print("Exception in tearDown: " + str(e))

    #Test of generall functionality and task order
    def test_timer(self):
        print("== test_timer ==")
        counter = TimerTests.Counter()
        self.t.start()
        self.t.add_task(lambda : counter.add(2), 1.0)
        self.t.add_task(lambda : counter.add(5), 2)
        self.t.add_task(lambda : counter.multiply(3), 1.5)
        print("after add")

        time.sleep(2.1)
        self.assertEqual(counter.get(), 11)

        self.t.add_task(lambda : counter.add(2), 1)
        self.t.add_task(lambda : counter.add(9), 5)
        self.t.add_task(lambda : counter.add(5), 3)
        print("after add")

        time.sleep(1.1)
        self.assertEqual(counter.get(), 13)
        time.sleep(2)
        self.assertEqual(counter.get(), 18)
        time.sleep(2)
        self.assertEqual(counter.get(), 27)

        self.t.add_task(lambda : counter.add(2), 100)
        self.t.add_task(lambda : counter.multiply(9), 120)
        self.t.add_task(lambda : counter.add(5), 130)

        time.sleep(0.5)
        self.assertEqual(counter.get(), 27)

        self.t.close_and_flush()
        self.assertEqual(counter.get(), 266)
        time.sleep(0.05)
        self.assertFalse(self.t.is_alive())

        self.t.add_task(lambda : counter.add(5), 0)
        time.sleep(0.1)
        self.assertEqual(counter.get(), 266)

    # Test of timer precision
    def test_timer_precision(self):
        print("== test_timer_precision ==")
        counter = TimerTests.Counter()
        self.t.start()

        self.t.add_task(lambda : counter.add(2), 1.25)
        time.sleep(1.2)
        self.assertEqual(counter.get(), 0)
        time.sleep(0.1)
        self.assertEqual(counter.get(), 2)

        
        self.t.add_task(lambda : counter.add(7), 1.25)
        self.t.add_task(lambda : counter.multiply(3), 1.5)
        time.sleep(1.2)
        self.assertEqual(counter.get(), 2)
        time.sleep(0.1)
        self.assertEqual(counter.get(), 9)
        time.sleep(0.15)
        self.assertEqual(counter.get(), 9)
        time.sleep(0.1)
        self.assertEqual(counter.get(), 27)

        self.t.close_and_flush()
        self.assertEqual(counter.get(), 27)

    # Test of timer exceptions
    def test_timer_exceptions(self):
        print("== test_timer_precision ==")
        counter = TimerTests.Counter()
        self.t.add_task(TimerTests.throw_something, 0.2)
        self.t.start()
        self.t.add_task(TimerTests.throw_something, 0.01)
        time.sleep(0.2)

        # The Timer should not be dead after exceptions in run()
        self.assertTrue(self.t.is_alive())
        self.t.add_task(lambda : counter.add(7), 0.01)
        time.sleep(0.1)
        self.assertEqual(counter.get(), 7)

        self.t.add_task(TimerTests.throw_something, 0.05)
        self.t.add_task(lambda : counter.add(2), 10)

        self.t.close_and_flush()
        time.sleep(0.1)
        self.assertFalse(self.t.is_alive())
        self.assertEqual(counter.get(), 9)


if __name__ == '__main__':
    unittest.main()
