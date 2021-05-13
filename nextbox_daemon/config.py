import os
import yaml
from pathlib import Path
import random
import string

import logging.handlers
import logging

from filelock import FileLock

from nextbox_daemon.consts import LOGGER_NAME, LOG_FILENAME, MAX_LOG_SIZE, CONFIG_PATH, \
    NEXTBOX_DEBIAN_PACKAGES

class Config(dict):
    def __init__(self, config_path, *va, **kw):
        super().__init__(*va, **kw)

        self.config_path = config_path
        self.config_lock_path = config_path + ".lock"
        self.config_lock = FileLock(self.config_lock_path, timeout=10)

        self.factory_config_path = "/srv/nextbox.factory.conf"
        self.factory_config_lock_path = self.factory_config_path + ".lock"
        self.factory_config_lock = FileLock(self.factory_config_lock_path, timeout=10)

        self.update({
            "config":    {
                "last_backup":  None,
                "last_restore": None,
                "http_port":    80,
                "https_port":   None,
                "hostname":     "nextbox",
                "log_lvl":      logging.DEBUG,

                "domain":       None,
                "email":        None,
                "desec_token":  None,

                "nk_token":     None,
                "serial":       None,
                
                "proxy_active": False,
                "proxy_domain": None,
                "proxy_port":   None,
                "dns_mode":     "off",
                "expert_mode":  False,

                "debian_package": "nextbox"
            }
        })
        self.load()
        self.manage_factory_config()

    def manage_factory_config(self):
        if Path(self.factory_config_path).exists():
            with self.factory_config_lock:
                with open(self.factory_config_path) as fd:
                    factory_conf = yaml.safe_load(fd)
        else:
            factory_conf = {}

        # if regular config contains 'nk_token' & 'serial' write factory-config if needed
        if self["config"]["nk_token"] and self["config"]["serial"]:
            if not "config" in factory_conf \
                or not factory_conf.get("config", {}).get("nk_token") \
                or not factory_conf.get("config", {}).get("serial"):

                factory_dct = {
                    "config": {
                        "nk_token": self["config"]["nk_token"],
                        "serial": self["config"]["serial"]
                    }
                }

                with self.factory_config_lock:
                    with open(self.factory_config_path, "w") as fd:
                        yaml.safe_dump(factory_dct, fd)

                log.info(f"wrote {self.factory_config_path} from regular config")

        # regular config has no valid 'nk_token' & 'serial', take from factory_conf (if available)
        elif not self["config"]["nk_token"] or not self["config"]["serial"]:
            nk_token = factory_conf.get("config", {}).get("nk_token")
            serial = factory_conf.get("config", {}).get("serial")
            if nk_token:
                self["config"]["nk_token"] = nk_token
            if serial:
                self["config"]["serial"] = serial

            if nk_token or serial:
                self.save()
                log.info(f"updated regular config from {self.factory_config_path}")
            else:
                log.warning(f"need, but could not get 'nk_token' or 'serial' from {self.factory_config_path}")


    def load(self):
        if not os.path.exists(self.config_path):
            print(f"config path: {self.config_path} not found...")
            return

        with self.config_lock:
            with open(self.config_path) as fd:
                loaded = yaml.safe_load(fd)
                try:
                    for key in loaded:
                        self.setdefault(key, {}).update(loaded[key])
                except TypeError:
                    pass

    def save(self):
        with self.config_lock:
            with open(self.config_path, "w") as fd:
                yaml.safe_dump(dict(self), fd)


def check_filesystem():
    """
    Check local filesystem "integrity":
    * existance of dirs: /srv/nextcloud, /srv/nextbox, /srv/apache2, 
                         /srv/mariadb, /srv/logdump, /srv/letsencrypt
    * existance and permissions (uid: 33 gid: 0): /srv/nextcloud/custom_apps
    * existance (and contents) of: /srv/nextbox/docker.env
    """

    # check/create dirs
    dirs_exist = ["/srv/nextcloud", "/srv/nextbox", "/srv/apache2", "/srv/backups", 
                  "/srv/mariadb", "/srv/logdump", "/srv/letsencrypt"]
    for p in dirs_exist:
        if not Path(p).exists():
            os.makedirs(p)
            print(f"created: {p}")

    # custom apps location
    custom_apps = Path("/srv/nextcloud/custom_apps")
    if not custom_apps.exists():
        os.makedirs(custom_apps)
        os.system(f"chown 33.0 /srv/nextcloud/custom_apps")
        print(f"created: {custom_apps} and set uid.gid to 33.0")

    # docker env (always during first startup)
    docker_env = Path("/srv/nextbox/docker.env")
    if not docker_env.exists():
        haystack = string.ascii_letters + string.digits
        random_pass_user = "".join(random.sample(haystack, 20))
        random_pass_root = "".join(random.sample(haystack, 20))
        with docker_env.open("w") as fd:
            fd.write("MYSQL_DATABASE=nextcloud\n")
            fd.write("MYSQL_USER=nextcloud\n")
            fd.write("MYSQL_HOST=db\n")
            fd.write(f"MYSQL_PASSWORD={random_pass_user}\n")
            fd.write(f"MYSQL_ROOT_PASSWORD={random_pass_root}\n")
        print("created /srv/nextbox/docker.env and contents")

    # make sure is correct: /etc/default/ddclient
    ddclient_env = Path("/etc/default/ddclient")
    content = "\n".join([
        'run_dhclient="false"',
        'run_ipup="true"',
        'run_daemon="true"',
        'daemon_interval="300"', ''
    ])
    if not ddclient_env.exists():
        with ddclient_env.open("w") as fd:
            fd.write(content)
        print("created /etc/default/ddclient")
    else:
        with ddclient_env.open("r") as fd:
            file_content = fd.read()
        if content != file_content:
            with ddclient_env.open("w") as fd:
                fd.write(content)
            print("re-written /etc/default/ddclient")
            
# helper for enviornment-file writing (/etc/default/nextbox-updater.service)
def write_nextbox_updater_env_file(path, pkg):
    with open(path, "w") as fd:
        fd.write(f"PACKAGE={pkg}\n")
        fd.write("DEBIAN_FRONTEND=noninteractive\n")
    return True

def check_filesystem_after_init(cfg):
    """
    Check integrity of filesystem after the config was initialized

    * /etc/default/nextbox-updater (environment file for nextbox-updater.service)
    """

    pkg = cfg["config"]["debian_package"]
    # illegal configuration, fallback to default 'stable' package
    if pkg not in NEXTBOX_DEBIAN_PACKAGES:
        pkg = "nextbox"
        # fix faulty configuration
        cfg["config"]["debian_package"] = pkg
        cfg.save()

    # nextbox-updater.service environment file
    nb_upd_env_path = "/etc/default/nextbox-updater"
    if not Path(nb_upd_env_path).exists():
        log.info(f"creating nextbox-updater.service env-file: {nb_upd_env_path}")
        write_nextbox_updater_env_file(nb_upd_env_path, pkg)
    else:
        write_file = False
        with open(nb_upd_env_path, "r") as fd:
            for line in fd:
                if "PACKAGE" in line:
                    try:
                        _, my_pkg = line.split("=")
                        if my_pkg.strip() != pkg:
                            write_file = True
                    except Exception as e:
                        log.error("failed extracting 'PACKAGE' from env file", exc_info=e)
                        log.info(f"re-creating faulty: {nb_upd_env_path}")
                        write_file = True
                    break
        if write_file:
            log.info(f"(re-)creating env-file: {nb_upd_env_path}")
            write_nextbox_updater_env_file(nb_upd_env_path, pkg)


# 1st filesystem integrity check
check_filesystem()

# logger setup + rotating file handler
log = logging.getLogger(LOGGER_NAME)
log.setLevel(logging.DEBUG)
log_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=5)
log.addHandler(log_handler)

# adapt logging-record-factory for a more condensed log
module_mapping = {
    "command_runner"    : "cmd_run",   "status_board"      : "board",
    "raw_backup_restore": "rbackup",   "proxy_tunnel"      : "ptun",
    "certificates"      : "certs",     "partitions"        : "parts",
}

level_mapping = {"CRITICAL": "[!]", "ERROR": "[E]", "WARNING": "[W]", 
    "INFO": "[i]", "DEBUG": "[D]" 
}

record_factory = logging.getLogRecordFactory()
def my_record_factory(*va, **kw):
    rec = record_factory(*va, **kw)
    rec.origin = module_mapping.get(rec.module, rec.module)
    rec.symlvl = level_mapping.get(rec.levelname, rec.levelname)
    return rec
# apply wrapped record factory
logging.setLogRecordFactory(my_record_factory)


# logging format
log_format = logging.Formatter("{asctime} {symlvl} {origin:<9} {message}", style='{')
log_handler.setFormatter(log_format)

# welcome banner (into log)
log.info("=" * 60)
log.info("====> starting nextbox-daemon")

# config load
cfg = Config(CONFIG_PATH)

# set log-level from config
log.setLevel(cfg["config"]["log_lvl"])

# 2nd filesystem integrity check, using loaded configuration
check_filesystem_after_init(cfg)