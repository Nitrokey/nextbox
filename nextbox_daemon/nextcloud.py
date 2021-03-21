from nextbox_daemon.config import log
from nextbox_daemon.command_runner import CommandRunner

class NextcloudError(Exception):
    pass


class Nextcloud:
    occ_cmd = ("docker", "exec", "-u", "www-data", 
        "nextbox-compose_app_1", "/var/www/html/occ", "-n", "--ansi",
        "--no-warnings")

    config_value_keys = ["overwritehost", "overwriteprotocol", "overwritewebroot", "overwritecondaddr"]
    config_list_keys = ["trusted_domains", "trusted_proxies"]

    def __init__(self):
        pass

    def run_cmd(self, *args):
        #log.debug(f"run (nextcloud): {self.occ_cmd + args}")
        cr = CommandRunner(self.occ_cmd + args, block=True)
        if cr.returncode != 0:
            cr.log_output()
            raise NextcloudError("failed to execute nextcloud:occ command")
        
        return cr.output[:-2]

    def get_config(self, key):
        return self.run_cmd("config:system:get", key)

    def set_config(self, key, data, idx=None):
        # set config list
        if key in self.config_list_keys:
            # single item in config list (data)
            if idx is not None:
                self.run_cmd("config:system:set", key, str(idx), "--value", data)
            # all items in data
            for idx, item in enumerate(data):
                self.run_cmd("config:system:set", key, str(idx), "--value", item)
        # set config string
        elif key in self.config_value_keys:
            self.run_cmd("config:system:set", key, "--type", "string", "--value", data)
        else:
            raise NextcloudError(f"unknown key: {key}")

    def delete_config(self, key):
        self.run_cmd("config:system:delete", key)

    def set_maintenance_on(self):
        return self.run_cmd("maintenance:mode", "--on")

    def set_maintenance_off(self):
        return self.run_cmd("maintenance:mode", "--off")
    
    def enable_nextbox_app(self):
        out = self.run_cmd("app:enable", "nextbox")
        out = " ".join(out)
        return "already" in out


if __name__ == "__main__":
    nc = Nextcloud()
    x = nc.get_config("trusted_domains")
    print(x)
    
    nc.delete_config("trusted_domains")
    x = nc.get_config("trusted_domains")
    print(x)

    nc.set_config("trusted_domains", ["192.168.*.*", "10.*.*.*", "172.18.*.*", "foo.nextbox.link"])
    x = nc.get_config("trusted_domains")
    print(x)

    # nc.set_maintenance_off()

    #nc.set_config("trusted_proxies", ["188.40.174.114"])
    # nc.set_config("overwritehost", "foo.nextbox.link")
    
    nc.set_config("overwriteprotocol", "https")
    nc.set_config("overwritecondaddr", r"^172\.18\.238\.1$")

    #x = nc.get_config("trusted_proxies")
    #print(x)
    #x = nc.get_config("overwriteprotocol")
    #print(x)
    #x = nc.get_config("overwritecondaddr")
    #print(x)


#  $CONFIG = array (
#  'trusted_proxies'   => ['10.0.0.1'],
#  'overwritehost'     => 'ssl-proxy.tld',
#  'overwriteprotocol' => 'https',
#  'overwritewebroot'  => '/domain.tld/nextcloud',
#  'overwritecondaddr' => '^10\.0\.0\.1$',
#);

