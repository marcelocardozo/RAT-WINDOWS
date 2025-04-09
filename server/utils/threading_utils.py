# server/utils/threading_utils.py
import threading
import queue
import logging
import time
import tkinter as tk
logger = logging.getLogger("server.threading_utils")
class TaskQueue:
    def __init__(self, max_workers=5):
        self.queue = queue.Queue()
        self.max_workers = max_workers
        self.workers = []
        self.running = True
        self._start_workers()
    def _start_workers(self):
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
    def _worker_loop(self):
        while self.running:
            try:
                task, args, kwargs = self.queue.get(timeout=1)
                try:
                    task(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Erro ao executar tarefa: {str(e)}")
                finally:
                    self.queue.task_done()
            except queue.Empty:
                continue
    def add_task(self, task, *args, **kwargs):
        if self.running:
            self.queue.put((task, args, kwargs))
    def stop(self, wait=True):
        self.running = False
        if wait:
            self.queue.join()
class UIThreadTask:
    def __init__(self, root):
        self.root = root
    def run_in_thread(self, task, callback=None):
        def thread_target():
            try:
                result = task()
                if callback:
                    self.root.after(0, lambda: callback(result))
            except Exception as e:
                logger.error(f"Erro na execução da tarefa: {str(e)}")
                if callback:
                    self.root.after(0, lambda: callback(None))
        thread = threading.Thread(target=thread_target, daemon=True)
        thread.start()
        return thread
    def schedule(self, delay, callback):
        return self.root.after(delay, callback)
    def cancel(self, job_id):
        if job_id:
            self.root.after_cancel(job_id)
class Debouncer:
    def __init__(self, delay_ms=500):
        self.delay_ms = delay_ms
        self.timer = None
        self.lock = threading.Lock()
    def debounce(self, root, callback):
        with self.lock:
            if self.timer is not None:
                root.after_cancel(self.timer)
            self.timer = root.after(self.delay_ms, callback)
    def cancel(self, root):
        with self.lock:
            if self.timer is not None:
                root.after_cancel(self.timer)
                self.timer = None
class Throttler:
    def __init__(self, delay_ms=1000):
        self.delay_ms = delay_ms
        self.last_execution = 0
        self.lock = threading.Lock()
    def throttle(self, root, callback):
        current_time = time.time() * 1000
        with self.lock:
            if current_time - self.last_execution >= self.delay_ms:
                self.last_execution = current_time
                callback()
                return None
            else:
                remaining = self.delay_ms - (current_time - self.last_execution)
                return root.after(int(remaining), callback)
