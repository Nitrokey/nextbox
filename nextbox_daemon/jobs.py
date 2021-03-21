from datetime import datetime as dt
from time import sleep
from pathlib import Path

import psutil

from nextbox_daemon.consts import *
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.config import log
from nextbox_daemon.nextcloud import Nextcloud, NextcloudError
from nextbox_daemon.raw_backup_restore import RawBackupRestore

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


class BackupRestoreJob(BaseJob):
    name = "BackupRestore"

    def __init__(self):
        self.ctrl = RawBackupRestore()
        self.iterator = None
        super().__init__(initial_interval=None)


    def _run(self, cfg, board, kwargs):

        # operation not running, means we start a backup: need a "tar_path" + "mode" (backup or restore)
        if not self.iterator and ("tar_path" not in kwargs or "mode" not in kwargs):
            msg = "Requested starting BackupRestore-Job without 'tar_path' and/or 'mode' arg"
            log.error(msg)
            board.messages.put(msg)
            return

        if not self.iterator and kwargs.get("mode") not in ["backup", "restore"]:
            msg = "'mode' arg needs to be either 'backup' or 'restore'"
            log.error(msg)
            board.messages.put(msg)
            return

        # ok, start backup/restore (set job-interval and return)
        if not self.iterator:
            #if not board.contains_key("backup"):
            board.update("backup_restore", {
                "state": "starting",
                "percent": "0",
                "who": "all", 
                "tar_path": kwargs["tar_path"],
                "what": "export" if kwargs["mode"] == "backup" else "import", 
                "mode": kwargs["mode"],
            })

            if kwargs["mode"] == "backup":
                self.iterator = self.ctrl.full_export(kwargs["tar_path"])
            else:
                self.iterator = self.ctrl.full_import(kwargs["tar_path"])
            self.interval = 5
            return

        # backup is running, update board with current state
        try:
            state, (who, what), percent = next(self.iterator)
            board.set("backup_restore", {
                "state": state,
                "who": who,
                "what": what,
                "percent": percent
            })
        except StopIteration:
            self.iterator = None
            self.interval = None


class EnableNextBoxAppJob(BaseJob):
    name = "EnableNextBoxApp"
    
    def __init__(self):
        self.nc = Nextcloud()
        super().__init__(initial_interval=5)

    def _run(self, cfg, board, kwargs):
        # just keep on trying to activate until it worked
        try:
            if self.nc.enable_nextbox_app():
                self.interval = 3600
        except NextcloudError:
            pass


class GenericStatusUpdateJob(BaseJob):
    name = "GenericStatusUpdate"

    def __init__(self):
        super().__init__(initial_interval=90)

    def _run(self, cfg, board, kwargs):

        pkg = cfg["config"]["debian_package"]
        cmd = f"dpkg -s {pkg}"
        cr = CommandRunner(cmd, block=True)
        for line in cr.output:
            if "Version:" in line:
                version = line.strip().split(":")[1]
                break
        board.set("pkginfo", {"version": version, "pkg": pkg})


class HardwareStatusUpdateJob(BaseJob):
    name = "HardwareStatusUpdate"

    def __init__(self):
        super().__init__(initial_interval=60)
    
    def _run(self, cfg, board, kwargs):
    
        temp = Path("/sys/class/hwmon/hwmon0/temp1_input").read_text().strip()

        board.set("hwinfo", {"temp": temp})

class TrustedDomainsJob(BaseJob):
    name = "TrustedDomains"
    
    static_entries = ["192.168.*.*", "10.*.*.*", "172.16.*.*", "172.18.*.*", "nextbox.local"]

    def __init__(self):
        self.nc = Nextcloud()
        super().__init__(initial_interval=90)

    def _run(self, cfg, board, kwargs):
        try:
            trusted_domains = self.nc.get_config("trusted_domains")
        except NextcloudError as e:
            log.warning("cannot get trusted_domains from nextcloud, not running?", exc_info=e)
            return False        

        default_entry = trusted_domains[0]

        entries = [default_entry] + self.static_entries[:]
        if cfg["config"].get("domain"):
            entries.append(cfg["config"]["domain"])

        if cfg["config"].get("proxy_active") and cfg["config"].get("proxy_domain"):
            entries.append(cfg["config"]["proxy_domain"])

        if any(entry not in trusted_domains for entry in entries):
            self.nc.set_config("trusted_domains", entries)

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

