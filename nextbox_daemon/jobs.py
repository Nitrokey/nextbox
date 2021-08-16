from datetime import datetime as dt
from time import sleep
from pathlib import Path
import os
import psutil
import apt
import docker

from nextbox_daemon.consts import *
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.config import log
from nextbox_daemon.nextcloud import Nextcloud, NextcloudError
from nextbox_daemon.certificates import Certificates
from nextbox_daemon.raw_backup_restore import RawBackupRestore
from nextbox_daemon.services import services
from nextbox_daemon.shield import shield
from nextbox_daemon.worker import BaseJob


class LEDJob(BaseJob):
    name = "LED"

    def __init__(self):
        super().__init__(initial_interval=10)

    def _run(self, cfg, board, kwargs):
        # check for maintenance mode
        nc = Nextcloud()
        if nc.is_maintenance:
            shield.set_led_state("maintenance")
        
        # check reachability
        #elif nc.check_reachability()[0]:
        #    ...
        
        # check if app container is up for more than 65secs
        elif not self.is_app_docker_up():
            shield.set_led_state("docker-wait")

        # all seems ready
        else:
            shield.set_led_state("ready")


    def is_app_docker_up(self):
        client = docker.APIClient()
        for item in client.containers():
            names = item.get("Names")
            if any("app_1" in name for name in names):
                if dt.now().timestamp() - item["Created"] > 75:
                    return True
        return False

class FactoryResetJob(BaseJob):
    name = "FactoryReset"

    def __init__(self):
        super().__init__(initial_interval=None)

    def _run(self, cfg=None, board=None, kwargs=None):
        
        # factory-reset is executed by systemd
        log.warning("Starting factory-reset operation")
        shield.set_led_state("factory-reset")
        services.start("nextbox-factory-reset")


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
            self.interval = 1
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
        # only enable, if nextcloud is installed
        if not self.nc.is_installed:
            log.debug("cannot enable nextbox-app - uninitialized nextcloud")
            return 
        
        # try to enable
        try:
            if self.nc.enable_nextbox_app():
                self.interval = 3600
                log.info("enabled nextcloud nextbox-app")
        except NextcloudError:
            pass


class SelfUpdateJob(BaseJob):
    name = "SelfUpdate"

    def __init__(self):
        super().__init__(initial_interval=1)
        
    def _run(self, cfg, board, kwargs):
        self.interval = None


        # ensure ddclient is running
        services.restart("ddclient")

        # ensure that neither updater nor factory-reset is masked
        services.unmask("nextbox-updater")
        services.unmask("nextbox-factory-reset")

        # ensure nextbox-compose is running
        services.start("nextbox-compose")

        shield.set_led_state("updating")

        log.info("running 'apt-get update'")
        # apt-get update
        cache = apt.cache.Cache()
        cache.update()
        cache.open()

        # which debian package shall be used?
        pkg = cfg["config"]["debian_package"]

        try:
            pkg_obj = cache[pkg]
        except KeyError:
            log.error(f"self-update failed: designated package: {pkg} not found!")
            log.error("falling back to 'nextbox' - retrying upgrade...")
            pkg = "nextbox"
        
            try:
                pkg_obj = cache[pkg]
            except KeyError:
                log.error("CRITICAL: failed to find 'nextbox' in apt-cache")
                # we should never ever end here, this means that the nextbox 
                # debian package is not available...
                # nextbox debian (ppa) repository not available ???!!
                return 

        # install package (i.e., other nextbox package is already installed)
        # will trigger for e.g., 'nextbox' to 'nextbox-testing' switching
        if not pkg_obj.is_installed:
            log.info(f"installing debian package: {pkg} (start service: nextbox-updater)")
            #services.stop("nextbox-compose")
            services.start("nextbox-updater")
        elif pkg_obj.is_upgradable:
            log.info(f"upgrading debian package: {pkg} (start service: nextbox-updater)")
            #services.stop("nextbox-compose")
            services.start("nextbox-updater")
        else:
            log.debug(f"no need to upgrade or install debian package: {pkg}")

        #job_queue.put("LED")

        #shield.set_led_state("ready")

class RenewCertificatesJob(BaseJob):
    name = "RenewCertificates"

    def __init__(self):
        super().__init__(initial_interval=3600*24)

    def _run(self, cfg, board, kwargs):
        c = Certificates()
        c.renew_certs()

class GenericStatusUpdateJob(BaseJob):
    name = "GenericStatusUpdate"

    def __init__(self):
        super().__init__(initial_interval=15)

    def _run(self, cfg, board, kwargs):
        self.interval = None

        pkg = cfg["config"]["debian_package"]

        try:
            cache = apt.cache.Cache()
            version = cache[pkg].installed.version
        except Exception as e:
            log.error(f"failed getting pkg-info for: {pkg}", exc_info=e)
            return
            
        board.set("pkginfo", {"version": version, "pkg": pkg})


class HardwareStatusUpdateJob(BaseJob):
    name = "HardwareStatusUpdate"

    def __init__(self):
        super().__init__(initial_interval=7200)
    
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
        self.interval = 900

        # only set trusted domains, if nextcloud is installed
        if not self.nc.is_installed:
            log.debug("cannot set trusted_domains - uninitialized nextcloud")
            self.interval = 15
            return False

        try:
            trusted_domains = self.nc.get_config("trusted_domains")
        except NextcloudError:
            log.warning("cannot get trusted_domains from nextcloud")
            self.interval = 15
            return False        

        default_entry = trusted_domains[0]

        entries = [default_entry] + self.static_entries[:]
        if cfg["config"].get("domain"):
            entries.append(cfg["config"]["domain"])

        if cfg["config"].get("proxy_active") and cfg["config"].get("proxy_domain"):
            entries.append(cfg["config"]["proxy_domain"])

        if any(entry not in trusted_domains for entry in entries):
            try:
                self.nc.set_config("trusted_domains", entries)
            except NextcloudError:
                log.warning("failed to write all trusted_domains")
                self.interval = 15


ACTIVE_JOBS = [
    LEDJob, FactoryResetJob, BackupRestoreJob, EnableNextBoxAppJob, 
    SelfUpdateJob, GenericStatusUpdateJob, HardwareStatusUpdateJob,
    TrustedDomainsJob, RenewCertificatesJob
]

