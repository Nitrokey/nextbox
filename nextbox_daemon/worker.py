
from queue import Empty
from threading import Thread
import threading
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
        """True, if this job has not been run since `> self.interval` seconds"""
        if self.interval is None:
            return False
        return (dt.now() - self.last_run).seconds > self.interval

    def run(self, cfg, board, kwargs):
        """Overridden Thread.run() is run inside the new thread after start()"""
        log.debug(f"starting worker job: {self.name}")
        self.last_run = dt.now()
        self._run(cfg, board, kwargs)
        log.debug(f"finished worker job: {self.name}")

    def _run(self, cfg, board, kwargs):
        """This is executed by the job-manager, where the work happens"""
        raise NotImplementedError()


class JobManager:
    def __init__(self, config, board):
        self.cfg = config
        self.jobs = { }
        self.board = board

    def register_job(self, job):
        """register job by `job.name` and construct their instances"""
        if job.name in self.jobs:
            log.warning(f"overwriting job (during register) with name: {job.name}")

        self.jobs[job.name] = job()
        log.info(f"registered job: {job.name}")

    def handle_job(self, job_name, job_kwargs):
        """check if job registered and run/call/execute task's: `run()`"""
        if job_name not in self.jobs:
            log.error(f"could not find job with name: {job_name}")
            return

        # run actual job
        try:
            self.jobs[job_name].run(self.cfg, self.board, job_kwargs)
        except Exception as e:
            log.error(f"failed running job: {job_name}", exc_info=e)

    def get_recurring_jobs(self):
        """return list-of-pairs [name, args] for due tasks"""
        return [ (name, None) for name, job in self.jobs.items() \
            if job.is_due() ]


class Worker(Thread):
    def __init__(self, job_queue, job_mgr, *v, **kw):
        super().__init__(*v, **kw)

        self.my_job_queue = job_queue
        self.job_mgr = job_mgr

    def run(self):
        # behold the mighty worker-loop
        while True:
            pending_jobs = []
            try:
                job = self.my_job_queue.get(timeout=1)
                
                if isinstance(job, str):
                    # handle job w/o args, comes as `name: str`
                    pending_jobs.append((job, None))
                else:
                    # already comes as `(name: str, args: tupel)`
                    pending_jobs.append(job)

            except Empty:
                # returns: list[job: tuple[str, tuple]]
                pending_jobs = self.job_mgr.get_recurring_jobs()

            # nothing to do => power nap
            if len(pending_jobs) == 0:
                sleep(0.5)
                continue
            
            for job_name, job_args in pending_jobs:
                # special job "exit" will stop the worker-queue
                if job_name == "exit":
                    log.info("exiting (background worker) by request")
                    return

                # finally handle (dispatch): `job_name` + `job_args`
                self.job_mgr.handle_job(job_name, job_args)


job_mgr = JobManager(cfg, board)
job_queue = Queue()
worker = Worker(job_queue, job_mgr)


