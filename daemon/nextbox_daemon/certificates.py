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
    
    config_dir = "/srv/letsencrypt"
    inside_docker_dir = "/etc/letsencrypt"
    apache_ssl_conf = "/srv/apache2/sites-available/nextbox-ssl.conf"
    apache_nossl_conf = "/srv/apache2/sites-available/000-default.conf"
    apache_enabled_dir = "/srv/apache2/sites-enabled"
    apache_restart = "docker exec nextbox-compose_app_1 apachectl graceful"

    apache_mods = ["rewrite", "ssl", "headers", "socache_shmcb"]
    apache_mods_available = "/srv/apache2/mods-available"
    apache_mods_enabled = "/srv/apache2/mods-enabled"

    acquire_cmd = "certbot --config-dir {config_dir} certonly --webroot --webroot-path /srv/nextcloud --email {email} --non-interactive --agree-tos -d {domain}"
    delete_cmd = "certbot --config-dir {config_dir} delete -d {domain}"
    list_cmd = "certbot --config-dir {config_dir} certificates"
    renew_cmd = "certbot --config-dir {config_dir} renew"

    # certbot --work-dir `pwd` --logs-dir . \
    #     --config-dir `pwd`/lets/ \
    #     --manual --text --preferred-challenges dns \
    #     --manual-auth-hook ./hook.sh --manual-cleanup-hook ./hook.sh \
    #     -d "cool-dns-auth.dedyn.io" \
    #     --agree-tos --non-interactive \
    #     --email cool-dns-auth@dadadada.33mail.com \
    #     certonly
    # ```

    desec_acquire_cmd = "certbot --config-dir {config_dir} --work-dir {config_dir} --manual --text --preferred-challenges dns --manual-auth-hook /usr/bin/nextbox-desec-hook.sh --manual-cleanup-hook /usr/bin/nextbox-desec-hook.sh --agree-tos --non-interactive --email {email} --domains {domain} --manual-public-ip-logging-ok certonly"
    desec_renew_cmd = "certbot --config-dir {config_dir} --work-dir {config_dir} --manual --text --preferred-challenges dns --manual-auth-hook /usr/bin/nextbox-desec-hook.sh --manual-cleanup-hook /usr/bin/nextbox-desec-hook.sh --agree-tos --non-interactive --manual-public-ip-logging-ok renew"
    desec_credentials_path = "/.dedynauth"

    # credentials:
    # ```
    # certbot --work-dir `pwd`/work --logs-dir /tmp/logs \
    #   --config-dir /tmp/test --manual --text \
    #   --preferred-challenges dns --manual-auth-hook ./hook.sh \
    #   --manual-cleanup-hook ./hook.sh -d "nextbox-dns-test.dedyn.io" \
    #   --agree-tos --non-interactive --email nextbox-dns-test@dadadada.33mail.com \
    #   --manual-public-ip-logging-ok certonly



    #### example output for 'list_cmd'
    # Found the following certs:
    #   Certificate Name: staticnextbox.dedyn.io
    #     Domains: staticnextbox.dedyn.io
    #     Expiry Date: 2021-06-05 14:10:45+00:00 (VALID: 80 days)
    #     Certificate Path: /srv/letsencrypt/live/staticnextbox.dedyn.io/fullchain.pem
    #     Private Key Path: /srv/letsencrypt/live/staticnextbox.dedyn.io/privkey.pem
    def get_local_certs(self):
        """Get the local certificate paths"""

        certs = []

        cr = CommandRunner(self.list_cmd.format(config_dir=self.config_dir), block=True)
        cur_cert = {}
        for line in cr.output:
            if "Certificate Name:" in line:
                cur_cert = {}
                cur_cert["name"] = line.split(":")[1].strip()
            elif "Domains:" in line:
                cur_cert["domains"] = line.split(":")[1].strip().split(" ")
            elif "Certificate Path:" in line:
                cur_cert["fullchain_path"] = line.split(":")[1].strip() \
                    .replace(self.config_dir, self.inside_docker_dir)
            elif "Private Key Path:" in line:
                cur_cert["privkey_path"] = line.split(":")[1].strip() \
                    .replace(self.config_dir, self.inside_docker_dir)
                certs.append(cur_cert)
            elif "Expiry Date:" in line:
                cur_cert["expiry"] = line.split(":", 1)[1].strip()

        
        return certs

    def delete_cert(self, domain):
        certs = self.get_local_certs()
        for cert in certs:
            if domain in cert["domains"]:
                cmd = self.delete_cmd.format(config_dir=self.config_dir, domain=domain)
                cr = CommandRunner(cmd, block=True)
                return cr.returncode == 0
        
        log.warning(f"{domain} not in certbot certificates for deletion found")
        return False

    def clear_certs(self):
        all_certs = self.get_local_certs()
        for cert in all_certs:
            self.delete_cert(cert["domains"][0])
        return True

    def get_cert(self, domain):
        certs = self.get_local_certs()
        for cert in certs:
            # if we try to get an already acquired domain, just return it
            if domain in cert["domains"]:
                return cert
        
    def write_dedyn_credentials(self, domain, token):
        with open(self.desec_credentials_path, "w") as fd:
            fd.write(f"export DEDYN_TOKEN={token}\n")
            fd.write(f"export DEDYN_NAME={domain}\n")
        log.info(f"wrote {self.desec_credentials_path}")


    def acquire_cert(self, domain, email):
        # here we try to acquire a new certificate using certbot
        dns_mode = cfg.get("config", {}).get("dns_mode")
        desec_token = cfg.get("config", {}).get("desec_token")

        # desec based certbot command (dns-based verification)
        if dns_mode == "desec_done":
            self.write_dedyn_credentials(domain, desec_token)
            cmd = self.desec_acquire_cmd.format(email=email, domain=domain, config_dir=self.config_dir)

        # others use reachability based verification
        elif dns_mode in ["config_done", "static_done"]:
            cmd = self.acquire_cmd.format(email=email, domain=domain, config_dir=self.config_dir, token=desec_token)     

        else:
            log.error("trying to acquire certificate w/o finished dns-config")
            return False

        # run certbot acquire command
        cr = CommandRunner(cmd, block=True)
        if cr.returncode == 0:
            return True

        # on fail log output
        log.error("could not acquire certificate")
        cr.log_output()
        return False

    def renew_certs(self):
        # here we try to acquire a new certificate using certbot
        dns_mode = cfg.get("config", {}).get("dns_mode")
        desec_token = cfg.get("config", {}).get("desec_token")
        https_port = cfg.get("config", {}).get("https_port")
        domain = cfg.get("config", {}).get("domain")

        # desec based certbot command (dns-based verification)
        if dns_mode == "desec_done":
            self.write_dedyn_credentials(domain, desec_token)
            cmd = self.desec_renew_cmd.format(config_dir=self.config_dir)

        # others use reachability based verification
        elif dns_mode in ["config_done", "static_done"]:
            cmd = self.renew_cmd.format(config_dir=self.config_dir, token=desec_token)         
               
        else:
            log.error("trying to renew certificate w/o activated certificate")
            return False

        # run certbot renew command
        cr = CommandRunner(cmd, block=True)
        if cr.returncode == 0:
            return True

        # on fail log output
        log.error("could not renew certificate(s)")
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
                log.info(f"enabled: {conf_avail_path.name}")

            if load_avail_path.exists() and not load_enabled_path.exists():
                load_enabled_path.symlink_to("../mods-available/" + load_avail_path.name)
                log.info(f"enabled: {load_avail_path.name}")


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

    def set_apache_config(self, ssl, run_reload=True):
        # config: either with or without ssl 
        conf = Path(self.apache_ssl_conf if ssl else self.apache_nossl_conf)
        enable_dir = Path(self.apache_enabled_dir)

        if not conf.exists():
            log.error(f"cannot activate {'ssl' if ssl else 'no-ssl'} - missing config: {conf}")
            return False
        
        # delete all enabled sites
        for path in enable_dir.iterdir():
            path.unlink()

        # create (ssl-)enable-site symlink
        enable_fn = conf.name
        enable_path = enable_dir / enable_fn
        enable_path.symlink_to("../sites-available/" + enable_fn)
        
        if run_reload and not self.reload_apache():
            log.error("failed apache (graceful) restart")
            log.error("rolling back to plain config...")
            self.set_apache_config(ssl=False, run_reload=False)
            return False
    
        return True


if __name__ == "__main__":
    pass

