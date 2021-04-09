TOOL_NAME = "nextbox"

API_VERSION = 1

LOGGER_NAME = TOOL_NAME
MAX_LOG_SIZE = 10 * 1024 * 1024

NEXTBOX_HDD_LABEL = "NextBoxHardDisk"

NEXTBOX_DEBIAN_PACKAGES = ["nextbox", "nextbox-testing", "nextbox-unstable"]


GET_EXT_IP4_URL = "http://v4.ipv6-test.com/api/myip.php"
GET_EXT_IP6_URL = "http://v6.ipv6-test.com/api/myip.php"

PROXY_REGISTER_URL = "https://nextbox.link/register"

CONFIG_PATH = "/srv/nextbox/nextbox.conf"

DDCLIENT_CONFIG_PATH = "/etc/ddclient/ddclient.conf"


LOG_FILENAME = "/var/log/nextbox.log"

DDCLIENT_BIN = "ddclient"


DYNDNS_MODES = ["desec", "desec_2", "static", "config", "off",
                "desec_done", "config_done", "static_done"]

AVAIL_CONFIGS = ["dns_mode", "desec_token", "email", "domain", "nk_token",
                 "proxy_active", "proxy_domain"]


MOUNT_BIN = "/bin/mount"
UMOUNT_BIN = "/bin/umount"



DYNDNS_DESEC_CAPTCHA = "https://desec.io/api/v1/captcha/"
DYNDNS_DESEC_REGISTER = "https://desec.io/api/v1/auth/"


SYSTEMD_RESOLVE_BIN = "/usr/bin/systemd-resolve"
SYSTEMCTL_BIN = "/usr/bin/systemctl"

