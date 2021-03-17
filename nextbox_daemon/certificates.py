from pathlib import Path

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.config import cfg, log

# https://ssl-config.mozilla.org/

CONF_TMPL = """
# generated 2021-03-17, Mozilla Guideline v5.6, Apache 2.4.41, OpenSSL 1.1.1d, intermediate configuration
# https://ssl-config.mozilla.org/#server=apache&version=2.4.41&config=intermediate&openssl=1.1.1d&guideline=5.6

# this configuration requires mod_ssl, mod_socache_shmcb, mod_rewrite, and mod_headers
<VirtualHost *:80>
    RewriteEngine On
    RewriteRule ^(.*)$ https://{HTTP_HOST}$1 [R=301,L]
</VirtualHost>

<VirtualHost *:443>
    SSLEngine on

    SSLCertificateFile      {FULLCHAIN_PATH}
    SSLCertificateKeyFile   {PRIVKEY_PATH}

    # enable HTTP/2, if available
    Protocols h2 http/1.1

    # HTTP Strict Transport Security (mod_headers is required) (63072000 seconds)
    Header always set Strict-Transport-Security "max-age=63072000"
</VirtualHost>

# intermediate configuration
SSLProtocol             all -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite          ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder     off
SSLSessionTickets       off

SSLUseStapling On
SSLStaplingCache "shmcb:logs/ssl_stapling(32768)"

"""

class Certificates:
    
    basedir = "/etc/letsencrypt"
    apache_ssl_conf = "/srv/apache2/sites-available/nextbox-ssl.conf"
    apache_nossl_conf = "/srv/apache2/sites-available/000-default.conf"
    apache_enabled_dir = "/srv/apache2/sites-enabled"
    apache_restart = "docker exec nextbox-compose_app_1 apachectl graceful"

    apache_mods = ["rewrite", "ssl", "headers", "socache_shmcb"]
    apache_mods_available = "/srv/apache2/mods-available"
    apache_mods_enabled = "/srv/apache2/mods-enabled"

    acquire_cmd = "certbot certonly --webroot --webroot-path /srv/nextcloud --email {email} --non-interactive --agree-tos -d {domain}"
    delete_cmd = "certbot delete -d {domain}"
    list_cmd = "certbot certificates"

    #### example output for 'list_cmd'
    # Found the following certs:
    #   Certificate Name: staticnextbox.dedyn.io
    #     Domains: staticnextbox.dedyn.io
    #     Expiry Date: 2021-06-05 14:10:45+00:00 (VALID: 80 days)
    #     Certificate Path: /etc/letsencrypt/live/staticnextbox.dedyn.io/fullchain.pem
    #     Private Key Path: /etc/letsencrypt/live/staticnextbox.dedyn.io/privkey.pem
    def get_local_certs(self):
        """Get the local certificate paths"""

        certs = []

        cr = CommandRunner(self.list_cmd, block=True)
        cur_cert = {}
        for line in cr.output:
            if "Certificate Name:" in line:
                cur_cert = {}
                cur_cert["name"] = line.split(":")[1].strip()
            elif "Domains:" in line:
                cur_cert["domains"] = line.split(":")[1].strip().split(" ")
            elif "Certificate Path:" in line:
                cur_cert["fullchain_path"] = line.split(":")[1].strip()
            elif "Private Key Path:" in line:
                cur_cert["privkey_path"] = line.split(":")[1].strip()
                certs.append(cur_cert)
        
        return certs

    def delete_cert(self, domain):
        certs = self.get_local_certs()
        for cert in certs:
            if domain in cert["domains"]:
                cr = CommandRunner(self.delete_cmd.format(domain=domain), block=True)
                return cr.returncode == 0
        
        log.warning(f"{domain} not in certbot certificates for deletion found")
        return False

    def get_cert(self, domain):
        certs = self.get_local_certs()
        for cert in certs:
            # if we try to get an already acquired domain, just return it
            if domain in cert["domains"]:
                return cert
        
    def acquire_cert(self, domain, email):
        # here we try to acquire a new certificate using certbot
        cmd = self.acquire_cmd.format(email=email, domain=domain)
        cr = CommandRunner(cmd, block=True)
        if cr.returncode == 0:
            return True

        # on fail log output
        log.error("could not acquire certificate")
        cr.log_output()
        return False

    def ensure_apache_mods(self):
        avail = Path(self.apache_mods_available)
        enabled = Path(self.apache_mods_enabled)

        for mod in self.apache_mods:
            conf_avail_path = (avail / (mod + ".conf"))
            load_avail_path = (avail / (mod + ".load"))
            conf_enabled_path = (enabled / (mod + ".conf"))
            load_enabled_path =  (enabled / (mod + ".load"))
            
            if conf_avail_path.exists() and not conf_enabled_path.exists():
                conf_enabled_path.symlink_to("../mods-available/" + conf_avail_path.name)
                log.info("enabled: {conf_avail_path.name}")

            if load_avail_path.exists() and not load_enabled_path.exists():
                load_enabled_path.symlink_to("../mods-available/" + load_avail_path.name)
                log.info("enabled: {load_avail_path.name}")


    def reload_apache(self):
        self.ensure_apache_mods()
        cr = CommandRunner(self.apache_restart, block=True)
        return cr.returncode == 0

    def write_apache_ssl_conf(self, domain, fullchain_path, privkey_path):
        conf = CONF_TMPL.format(
            HTTP_HOST=domain, 
            FULLCHAIN_PATH=fullchain_path, 
            PRIVKEY_PATH=privkey_path
        )
        with open(self.apache_ssl_conf, "w") as fd:
            fd.write(conf)

        return True

    def set_apache_config(self, ssl):
        # config: either with or without ssl 
        conf = Path(self.apache_ssl_conf if ssl else self.apache_nossl_conf)
        enable_dir = Path(self.apache_enabled_dir)

        if not conf.exists():
            log.error(f"cannot activate {'ssl' if ssl else 'no-ssl'} - missing config: {conf}")
            return False
        
        # delete all enabled sites
        for path in enable_dir.iterdir():
            path.unlink()

        # create ssl-enable-site symlink
        enable_fn = conf.name
        enable_path = enable_dir / enable_fn
        enable_path.symlink_to("../sites-available/" + enable_fn)
        
        if not self.reload_apache():
            log.error("failed apache (graceful) restart")
            return False
    
        return True


if __name__ == "__main__":
    c = Certificates()

    c.set_apache_config(ssl=False)

    # print(c.get_local_certs())

    # cert = c.get_cert("staticnextbox.dedyn.io")

    # c.write_apache_ssl_conf(cert["domains"][0], cert["fullchain_path"], cert["privkey_path"])

    # print(c.set_apache_config(ssl=True))

