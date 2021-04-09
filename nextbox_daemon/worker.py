
from queue import Empty
from threading import Thread
from time import sleep
import logging
from queue import Queue
from datetime import datetime as dt

from nextbox_daemon.config import log, cfg
from nextbox_daemon.status_board import board


class BaseJob:
    name = None

    def __init__(self, initial_interval):
        self.interval = initial_interval
        self.last_run = dt.now()

    def is_due(self):
        if self.interval is None:
            return False
        return (dt.now() - self.last_run).seconds > self.interval

    def run(self, cfg, board, kwargs):
        log.debug(f"starting worker job: {self.name}")
        self.last_run = dt.now()
        self._run(cfg, board, kwargs)
        log.debug(f"finished worker job: {self.name}")

    def _run(self, cfg, board, kwargs):
        raise NotImplementedError()


class JobManager:
    def __init__(self, config, board):
        self.cfg = config
        self.jobs = { }
        self.board = board

    def register_job(self, job):
        log.info(f"registering job {job.name}")
        if job.name in self.jobs:
            log.warning(f"overwriting job (during register) with name: {job.name}")
        self.jobs[job.name] = job()


    def handle_job(self, job_name, job_kwargs):
        if job_name not in self.jobs:
            log.error(f"could not find job with name: {job_name}")
            return

        # run actual job
        try:
            self.jobs[job_name].run(self.cfg, self.board, job_kwargs)
        except Exception as e:
            log.error(f"failed running job: {job_name}")
            log.error(msg="EXC", exc_info=e)

    def get_recurring_job(self):
        for name, job in self.jobs.items():
            if job.is_due():
                return name


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


