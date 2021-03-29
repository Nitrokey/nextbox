
from queue import Empty
from threading import Thread
from time import sleep
import logging
from queue import Queue

from nextbox_daemon.config import log, cfg
from nextbox_daemon.jobs import JobManager
from nextbox_daemon.status_board import board

class Worker(Thread):
    def __init__(self, job_queue, job_mgr, *v, **kw):
        super().__init__(*v, **kw)

        self.my_job_queue = job_queue
        self.job_mgr = job_mgr

    def run(self):
        while True:
            try:
                job = self.my_job_queue.get(timeout=1)
                
                # put either "jobname" or ("jobname", "args") into job_queue 
                if job is None:
                    job_name = None
                    job_args = None
                
                elif isinstance(job, str):
                    job_name = job
                    job_args = None
                
                else:
                    job_name, job_args = job

            except Empty:
                job_name = self.job_mgr.get_recurring_job()
                job_args = None

            if job_name is None:
                sleep(1)
                continue

            
            # special job "exit" will stop the worker-queue
            if job_name == "exit":
                break

            self.job_mgr.handle_job(job_name, job_args)


job_mgr = JobManager(cfg, board)
job_queue = Queue()
worker = Worker(job_queue, job_mgr)


