#  Timer.py
#  
#  Copyright 2019 Johannes Kern <johannes.kern@fau.de>
#  
#  

import threading
import bisect
from time import time
import Logging

logger = Logging.get_logger(__name__)

class Timer(threading.Thread):
    class Task:
        def __init__(self, run, timestamp):
            self.run = run
            self.timestamp = timestamp

        def __lt__(self, other):
            return self.timestamp >= other.timestamp

        def __gt__(self, other):
            return self.timestamp <= other.timestamp

    class PoisonPill(Exception):
        @staticmethod
        def take_it():
            raise Timer.PoisonPill()

    def __init__(self):
        super().__init__()
        self._queue = []
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def run(self):
        with self._lock:
            while True:
                while len(self._queue) > 0 and self._queue[-1].timestamp <= time():
                    task = self._queue.pop()
                    self._lock.release()
                    try:
                        task.run()
                    except Timer.PoisonPill:
                        logger.info("Catched PoisonPill, exiting now.")
                        self._lock.acquire()
                        return
                    except Exception as e:
                        logger.warning("Exception raised while running timer task: " + str(e))
                    self._lock.acquire()
                time_to_wait = None
                if len(self._queue) > 0:
                    time_to_wait = self._queue[-1].timestamp - time()
                self._cond.wait(time_to_wait)

    def add_task(self, action, rel_time):
        cur_time = time()
        with self._lock:
            task = Timer.Task(action, cur_time + rel_time)
            bisect.insort(self._queue, task)
            self._cond.notify()
            return task

    def execute_immediately(self, task):
        with self._lock:
            self._queue.remove(task)
            try:
                task.run()
            except Exception as e:
                logger.warning("Exception raised while running timer task: " + str(e))

    def close_and_flush(self):
        with self._lock:
            # execute all timer tasks immediately
            while len(self._queue) > 0:
                task = self._queue.pop()
                self._lock.release()
                try:
                    task.run()
                except Exception as e:
                    logger.warning("Exception raised while running timer task: " + str(e))
                self._lock.acquire()
            # insert poison pill into queue to let the timer thread die after wakeup
            self._queue.append(Timer.Task(Timer.PoisonPill.take_it, 0))
            self._cond.notify()
