import os
import yaml
from pathlib import Path
import random
import string

import logging.handlers
import logging

from filelock import FileLock

from nextbox_daemon.consts import LOGGER_NAME, LOG_FILENAME, MAX_LOG_SIZE, CONFIG_PATH

class Config(dict):
    def __init__(self, config_path, *va, **kw):
        super().__init__(*va, **kw)

        self.config_path = config_path
        self.config_lock_path = config_path + ".lock"
        self.config_lock = FileLock(self.config_lock_path, timeout=10)

        self.update({
            "config":    {
                "last_backup":  None,
                "last_restore": None,
                "http_port":    80,
                "https_port":   None,
                "hostname":     "NextBox",
                "log_lvl":      logging.INFO,

                "domain":       None,
                "email":        None,
                "desec_token":  None,
                "nk_token":     None,
                "proxy_active": False,
                "proxy_domain": None,
                "proxy_port":   None,
                "dns_mode":     "off",
                "expert_mode":  False,

                "debian_package": "nextbox"
            }
        })
        self.load()

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
    - existance of dirs: /srv/nextcloud, /srv/nextbox, /srv/apache2, /srv/mariadb
    - existance and permissions (uid: 33 gid: 0): /srv/nextcloud/custom_apps
    - existance (and contents) of: /srv/nextbox/docker.env
    """

    # check/create dirs
    dirs_exist = ["/srv/nextcloud", "/srv/nextbox", "/srv/apache2", "/srv/backups", 
                  "/srv/mariadb", "/srv/logdump", "/etc/letsencrypt"]
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

# check filesystem and do adjustments, if needed
check_filesystem()

# logger setup + rotating file handler
log = logging.getLogger(LOGGER_NAME)
log.setLevel(logging.DEBUG)
log_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=MAX_LOG_SIZE, backupCount=5)
log.addHandler(log_handler)
log_format = logging.Formatter("{asctime} {module} {levelname} => {message}", style='{')
log_handler.setFormatter(log_format)

log.info("starting nextbox-daemon")

# config load
cfg = Config(CONFIG_PATH)
