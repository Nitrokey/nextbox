from datetime import datetime as dt
from time import sleep
from pathlib import Path
import os
import psutil
import apt
import docker
import requests

from nextbox_daemon.consts import *
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.config import log
from nextbox_daemon.utils import nextbox_version
from nextbox_daemon.nextcloud import Nextcloud, NextcloudError
from nextbox_daemon.certificates import Certificates
from nextbox_daemon.dns_manager import DNSManager
from nextbox_daemon.raw_backup_restore import RawBackupRestore
from nextbox_daemon.proxy_tunnel import ProxyTunnel, ProxySetupError
from nextbox_daemon.services import services
from nextbox_daemon.shield import shield
from nextbox_daemon.worker import BaseJob
from nextbox_daemon.docker_control import DockerControl


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
        # elif nc.check_reachability()[0]:
        #    ...

        # check if app container is up for more than 20secs and nextcloud is initialized
        # 20 secs because containers restart on boot (check if nextbox-updater.service is still necessary)
        elif not self.is_app_docker_up():
            log.info(f"docker up {self.is_app_docker_up()} is_inst: {nc.is_installed}")

            shield.set_led_state("docker-wait")

        # all seems ready
        else:
            shield.set_led_state("ready")

    def is_app_docker_up(self):
        client = docker.APIClient()
        for item in client.containers():
            names = item.get("Names")
            if any("app_1" in name for name in names):
                if dt.now().timestamp() - item["Created"] > 20:
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


class DynDNSUpdateJob(BaseJob):
    name = "DynDNSUpdate"

    def __init__(self):
        super().__init__(initial_interval=5 * 60)

    def _run(self, cfg, board, kwargs):
        token = cfg["config"]["desec_token"]
        dns_mode = cfg["config"]["dns_mode"]
        domain = cfg["config"]["domain"]

        if dns_mode not in ["desec_done", "off"]:
            if not services.is_active("ddclient"):
                services.restart("ddclient")
                services.enable("ddclient")
            return

        if dns_mode == "off":
            if services.is_active("ddclient"):
                services.stop("ddclient")
                services.disable("ddclient")
            return

        if dns_mode == "desec_done":
            if services.is_active("ddclient"):
                services.stop("ddclient")
                services.disable("ddclient")

            dns = DNSManager()
            ipv4 = dns.get_ipv4()
            ipv6 = dns.get_ipv6()

            headers = {"Authorization": f"Token {token}"}

            params = {"hostname": domain}
            if ipv4:
                params["myipv4"] = ipv4
            if ipv6:
                params["myipv6"] = ipv6

            res = requests.get(
                "https://update.dedyn.io", params=params, headers=headers
            )

            if res.ok:
                log.info(
                    f"updated deSEC IPv4 ({ipv4}) and IPv6 ({ipv6}) address for '{domain}'"
                )
            else:
                log.warning(
                    f"failed updating IPs ({ipv4} & {ipv6}) for domain: '{domain}'"
                )
                log.debug(
                    f"result: {res.text} status_code: {res.status_code} url: {res.url}"
                )


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

        if not self.iterator and kwargs.get("mode") not in [
            "backup",
            "restore",
        ]:
            msg = "'mode' arg needs to be either 'backup' or 'restore'"
            log.error(msg)
            board.messages.put(msg)
            return

        # ok, start backup/restore (set job-interval and return)
        if not self.iterator:
            # if not board.contains_key("backup"):
            board.set(
                "backup_restore",
                {
                    "state": "starting",
                    "percent": "0",
                    "who": "all",
                    "tar_path": kwargs["tar_path"],
                    "what": ("export" if kwargs["mode"] == "backup" else "import"),
                    "mode": kwargs["mode"],
                },
            )

            if kwargs["mode"] == "backup":
                self.iterator = self.ctrl.full_export(kwargs["tar_path"])
            else:
                self.iterator = self.ctrl.full_import(kwargs["tar_path"])
            self.interval = 1
            return

        # backup is running, update board with current state
        try:
            state, (who, what), percent = next(self.iterator)
            board.set(
                "backup_restore",
                {"state": state, "who": who, "what": what, "percent": percent},
            )
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

        # if the custom-dns-config is active, ensure ddclient is up
        if cfg["config"]["dns_mode"] == "config_done" and not services.is_active(
            "ddclient"
        ):
            services.restart("ddclient")

        # ensure that neither updater nor factory-reset are masked (paranoia!)
        services.unmask("nextbox-updater")
        services.unmask("nextbox-factory-reset")

        # make sure userconfig is off
        services.stop("userconfig")
        services.disable("userconfig")
        services.mask("userconfig")

        # log a welcome + version
        log.info(
            f"Hello World - I am NextBox - call me: v{nextbox_version()} - let'sa gooo"
        )

        # update/upgrade now
        shield.set_led_state("updating")

        # log.info("running 'apt-get update'")
        # cache = apt.cache.Cache()
        # cache.update()
        # cache.open()

        # which debian package
        # pkg = cfg["config"]["debian_package"]

        # try:
        #    pkg_obj = cache[pkg]
        # except KeyError:
        #    log.error(f"self-update failed: designated package: {pkg} not found!")
        #    log.error("falling back to 'nextbox' - retrying upgrade...")
        #    pkg = "nextbox"

        #    try:
        #        pkg_obj = cache[pkg]
        #    except KeyError:
        #        log.error("CRITICAL: failed to find 'nextbox' in apt-cache")
        #        # we should never ever end here, this means that the nextbox
        #        # debian package is not available...
        #        # nextbox debian (ppa) repository not available ???!!
        #        return

        # install package (i.e., other nextbox package is already installed)
        # will trigger for e.g., 'nextbox' to 'nextbox-testing' switching
        # if not pkg_obj.is_installed:
        #    log.info(f"installing debian package: {pkg} (start service: nextbox-updater)")
        #    services.start("nextbox-updater")
        # elif pkg_obj.is_upgradable:
        #    log.info(f"upgrading debian package: {pkg} (start service: nextbox-updater)")
        #    services.start("nextbox-updater")
        # else:
        #    log.debug(f"no need to upgrade or install debian package: {pkg}")

        # job_queue.put("LED")

        # shield.set_led_state("ready")


class RenewCertificatesJob(BaseJob):
    name = "RenewCertificates"

    def __init__(self):
        # run every 20h
        super().__init__(initial_interval=3600 * 20)

    def _run(self, cfg, board, kwargs):
        c = Certificates()
        c.renew_certs()
        c.reload_apache()


class EnableHTTPSJob(BaseJob):
    name = "EnableHTTPS"

    def __init__(self):
        super().__init__(initial_interval=None)

    def _run(self, cfg, board, kwargs):
        board.set(
            "tls",
            {
                "what": "enable",
                "state": "running",
            },
        )

        certs = Certificates()
        domain = cfg.get("config", {}).get("domain")
        email = cfg.get("config", {}).get("email")

        if not domain or not email:
            log.error(f"cannot enable tls, domain: '{domain}' email: '{email}'")
            board.set(
                "tls",
                {
                    "what": "domain-or-email",
                    "state": "fail",
                },
            )
            return False

        my_cert = certs.get_cert(domain)
        if not my_cert:
            log.warning(f"could not get local certificate for: {domain}, acquiring...")
            if not certs.acquire_cert(domain, email):
                msg = f"Failed to acquire {domain} with {email}"
                log.error(msg)
                board.set(
                    "tls",
                    {
                        "what": "acquire",
                        "state": "fail",
                    },
                )
                return False
            log.info(f"acquired certificate for: {domain} with {email}")
            my_cert = certs.get_cert(domain)

        certs.write_apache_ssl_conf(
            my_cert["domains"][0],
            my_cert["fullchain_path"],
            my_cert["privkey_path"],
        )

        if not certs.set_apache_config(ssl=True):
            board.set(
                "tls",
                {
                    "what": "apache-config",
                    "state": "fail",
                },
            )
            log.error("failed enabling ssl configuration for apache")
            return False

        log.info(f"activated https for apache using: {domain}")

        cfg["config"]["https_port"] = 443
        cfg["config"]["email"] = email
        cfg.save()

        board.set(
            "tls",
            {
                "what": "enable",
                "state": "success",
            },
        )

        # we need to "re-wire" the proxy to port 443 on activated TLS
        add_msg = ""
        if cfg["config"]["proxy_active"]:
            subdomain = cfg["config"]["proxy_domain"].split(".")[0]
            scheme = "https"
            token = cfg["config"]["nk_token"]
            proxy_tunnel = ProxyTunnel()
            try:
                proxy_port = proxy_tunnel.setup(token, subdomain, scheme)
            except ProxySetupError as e:
                log.error("register at proxy-server error", exc_info=e)
            except Exception as e:
                log.error("unexpected error during proxy setup", exc_info=e)

            cfg["config"]["proxy_port"] = proxy_port
            cfg.save()


class HardwareStatusUpdateJob(BaseJob):
    name = "HardwareStatusUpdate"

    def __init__(self):
        super().__init__(initial_interval=7200)

    def _run(self, cfg, board, kwargs):
        temp = Path("/sys/class/hwmon/hwmon0/temp1_input").read_text().strip()

        board.set("hwinfo", {"temp": temp})


class TrustedDomainsJob(BaseJob):
    name = "TrustedDomains"

    static_entries = [
        "192.168.*.*",
        "10.*.*.*",
        "172.16.*.*",
        "172.18.*.*",
        "nextbox.local",
    ]

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


class ReIndexAllFilesJob(BaseJob):
    """
    Job to re-index all files once a day, so that files added
    by different means than the web interface (eg. ssh) will be
    visible after at most a day.
    """

    name = "ReIndexAllFiles"

    def __init__(self):
        self.nc = Nextcloud()
        super().__init__(initial_interval=900)

    def _run(self, cfg, board, kwargs):
        # run once a day (+ 10k secs)
        self.interval = 96400

        # only re-index files, if nextcloud is installed
        if not self.nc.is_installed:
            log.debug("cannot re-index all files - uninitialized nextcloud")
            self.interval = 15
            return False

        try:
            # re-index all files
            self.nc.run_cmd("files:scan", "--shallow", "--all")
        except NextcloudError:
            log.warning("cannot re-index files")
            self.interval = 15
            return False


class PurgeOldDockerImagesJob(BaseJob):
    """
    Job to periodically purge old images using
    DockerControl.purge_old_images
    """

    name = "PurgeOldDockerImages"

    def __init__(self):
        super().__init__(initial_interval=600)

    def _run(self, cfg, board, kwargs):
        # run once a week
        self.interval = 604800
        DockerControl().purge_old_images()


class OccUpgradeJob(BaseJob):
    """
    Executes occ upgrade command on startup.
    This removes the necessity for users to upgrade manually.
    """

    name = "OccUpgrade"

    def __init__(self):
        self.nc = Nextcloud()
        super().__init__(initial_interval=60)

    def _run(self, cfg, board, kwargs):
        self.interval = None

        if not self.nc.is_installed:
            log.debug("cannot occ upgrade - uninitialized nextcloud")
            self.interval = 20
            return False

        try:
            self.nc.run_cmd("upgrade")
        except NextcloudError:
            log.warning("cannot occ upgrade")
            self.interval = 20
            return False


class AdminNotification(BaseJob):
    """
    Send notifications to users part of the admin group.
    To send a message append it to global `admin_messages` list.
    """

    name = "AdminNotification"

    def __init__(self):
        self.nc = Nextcloud()
        self.update_notification_sent = False
        super().__init__(initial_interval=180)

    def _run(self, cfg, board, kwargs):
        if not self.nc.is_installed:
            log.debug("cannot send admin notifications - uninitialized nextcloud")
            self.interval = 20
            return False

        try:
            # reactivate on release before next update (debian 12)

            # if not self.update_notification_sent:
            #     self._send_update_notification()
            #     self.update_notification_sent = True
            for message in admin_messages.copy():
                message_header = "NextBox"
                for user in self._get_admin_users():
                    self.nc.run_cmd(
                        "notification:generate",
                        "-l",
                        message,
                        user,
                        message_header,
                    )
                admin_messages.remove(message)

            self.interval = 300
        except NextcloudError:
            log.warning("cannot send admin notifications")
            self.interval = 20
            return False

    def _get_admin_users(self):
        groups = self.nc.run_cmd("group:list")
        groups = ",".join(groups).replace(" ", "").replace("-", "").split(",")
        log.debug(f"group list output: {groups}")
        admin_group = False
        admins = []
        for ele in groups:
            if ele == "admin:":
                admin_group = True
                continue
            if admin_group:
                if ele[-1] == ":":
                    break
                admins.append(ele)
        return admins

    def _send_update_notification(self):
        version_file = Path("/etc/debian_version")
        with version_file.open() as fd:
            version = fd.read().split(".")[0]
        if version != "10":
            return

        admins = self._get_admin_users()
        log.debug(f"admin users: {admins}")

        message_header = "NextBox Major System Update: Please read"
        message_body = "Your NextBox is receiving a major system update. To make sure everything goes smoothly, please start the process manually as soon as possible in the NextBox App System Settings. Otherwise the update will be automatically installed within the upcoming weeks. Please refer to the Nitrokey blog post for further information."

        for user in admins:
            self.nc.run_cmd(
                "notification:generate",
                "-l",
                message_body,
                user,
                message_header,
            )


class AutomaticDebianUpdate(BaseJob):
    """
    Send notification warning about update.
    After 1 hour start update.
    """

    name = "AutomaticDebianUpdate"

    def __init__(self):
        self.nc = Nextcloud()
        self.startup = True
        super().__init__(initial_interval=1)

    def _run(self, cfg, board, kwargs):
        self.interval = None

        # only run if debian version needs to be updated
        version_file = Path("/etc/debian_version")
        with version_file.open() as fd:
            version = fd.read().split(".")[0]
        if version != "10":
            return

        # on startup send a warning message to admins and wait 1h
        if self.startup:
            admin_messages.append(
                "Warning: Automatic Debian Update in one hour! Please make sure you have sufficient backups, in case anything goes wrong!"
            )
            self.startup = False
            self.interval = 3600
            return

        log.info("starting automatic debian update!")
        shield.set_led_state("updating")
        cr = os.system("nohup /usr/bin/nextbox-update-debian.sh")
        if cr != 0:
            log.error(
                "Automatic debian update failed! Please refer to Nitrokey support!"
            )
            admin_messages.append(
                "Automatic Debian Update failed! Please refer to Nitrokey support!"
            )


admin_messages: list[str] = []

ACTIVE_JOBS = [
    LEDJob,
    FactoryResetJob,
    BackupRestoreJob,
    EnableNextBoxAppJob,
    SelfUpdateJob,
    HardwareStatusUpdateJob,
    TrustedDomainsJob,
    RenewCertificatesJob,
    DynDNSUpdateJob,
    EnableHTTPSJob,
    ReIndexAllFilesJob,
    PurgeOldDockerImagesJob,
    OccUpgradeJob,
    AdminNotification,
    AutomaticDebianUpdate,
]
