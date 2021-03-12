TOOL_NAME = "nextbox"

API_VERSION = 1

LOGGER_NAME = TOOL_NAME
MAX_LOG_SIZE = 2**30

NEXTBOX_HDD_LABEL = "NextBoxHardDisk"

GET_EXT_IP4_URL = "http://v4.ipv6-test.com/api/myip.php"
GET_EXT_IP6_URL = "http://v6.ipv6-test.com/api/myip.php"

PROXY_REGISTER_URL = "https://nextbox.link/register"
PROXY_KEY_PATH = "/srv/nextbox/proxy_key"
PROXY_PUBKEY_PATH = PROXY_KEY_PATH + ".pub"
PROXY_KEYGEN_CMD = ["ssh-keygen", "-b", "4096", "-t", "rsa", "-f", PROXY_KEY_PATH, "-q", "-N", ""]

CONFIG_PATH = "/srv/nextbox/nextbox.conf"

LOG_FILENAME = "/var/log/nextbox.log"

DDCLIENT_CONFIG_PATH = "/etc/ddclient/ddclient.conf"
DDCLIENT_BIN = "ddclient"
DDCLIENT_SERVICE = "ddclient.service"

NEXTBOX_SERVICE = "nextbox-daemon.service"
COMPOSE_SERVICE = "nextbox-compose.service"

DYNDNS_MODES = ["desec", "desec_2", "static", "config", "off",
                "desec_done", "config_done", "static_done"]

AVAIL_CONFIGS = ["dns_mode", "desec_token", "email", "domain", "nk_token",
                 "proxy_active", "proxy_domain"]

DYNDNS_DESEC_CAPTCHA = "https://desec.io/api/v1/captcha/"
DYNDNS_DESEC_REGISTER = "https://desec.io/api/v1/auth/"


SYSTEMD_RESOLVE_BIN = "/usr/bin/systemd-resolve"

SYSTEMCTL_BIN = "/usr/bin/systemctl"

UPDATE_NEXTBOX_APP_CMD = ["/snap/bin/nextcloud-nextbox.occ",
                          "app:update", "-n", "nextbox", "--ansi"]
INSTALL_NEXTBOX_APP_CMD = ["/snap/bin/nextcloud-nextbox.occ",
                          "app:install", "-n", "nextbox", "--ansi"]



ENABLE_HTTPS_BIN = "/snap/bin/nextcloud-nextbox.enable-https"
DISABLE_HTTPS_BIN = "/snap/bin/nextcloud-nextbox.disable-https"
BACKUP_EXPORT_BIN = "/snap/bin/nextcloud-nextbox.export"
BACKUP_IMPORT_BIN = "/snap/bin/nextcloud-nextbox.import"

CERTBOT_CERTS_PATH = "/var/snap/nextcloud-nextbox/current/certs/certbot/config/live"
CERTBOT_BACKUP_PATH = "/var/snap/nextcloud-nextbox/current/certs/certbot/config/live.bak"

OCC_BIN = "/snap/bin/nextcloud-nextbox.occ"
MOUNT_BIN = "/bin/mount"
UMOUNT_BIN = "/bin/umount"



###
### certbot certonly --webroot --webroot-path /srv/nextcloud --email {email} --non-interactive --agree-tos -d {domain}
###
### certificates at /etc/letsencrypt
###
### delete certificates: rm -rf /etc/letsencrypt ?
###        -> /etc/letsencrypt/archive /etc/letsencrypt/live