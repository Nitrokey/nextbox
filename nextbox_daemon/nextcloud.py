from pathlib import Path

from nextbox_daemon.config import log
from nextbox_daemon.command_runner import CommandRunner

class NextcloudError(Exception):
    pass


class Nextcloud:
    """Nextcloud administration, wrapping nextcloud's `occ` cli-tool"""

    occ_cmd = ("docker", "exec", "-u", "www-data", 
        "nextbox-compose_app_1", "/var/www/html/occ", "-n", "--ansi",
        "--no-warnings")

    config_value_keys = ["overwritehost", "overwriteprotocol", "overwritewebroot", "overwritecondaddr"]
    config_list_keys = ["trusted_domains", "trusted_proxies"]

    can_install_path = "/srv/nextcloud/config/CAN_INSTALL"

    @property
    def is_installed(self):
        """If `can_install_path` exists, nextcloud's initialization is not done"""
        return not Path(self.can_install_path).exists()

    def run_cmd(self, *args):
        """
        Run `occ` command with given `args`

        * raise `NextcloudError` on error
        * return (merged stdin + stderr) output on success
        """
        cr = CommandRunner(self.occ_cmd + args, block=True)
        if cr.returncode != 0:
            cr.log_output()
            raise NextcloudError("failed to execute nextcloud:occ command")
        
        return cr.output[:-2]

    def get_config(self, key):
        """Return config value identified by `key`"""
        return self.run_cmd("config:system:get", key)

    def set_config(self, key, data, idx=None):
        """
        Set config value identified by `key` to `data`.
        
        * determining the type is based on `key` in any of `config_{list,value}_keys`.
        * `idx: int` may be passed to set just one item of a list/array config
        * `data: [list, str]` strictly based on `key`
        """
        # set config list
        if key in self.config_list_keys:
            # single item in config list (data as item at `idx` in list)
            if idx is not None:
                self.run_cmd("config:system:set", key, str(idx), "--value", data)
                return 
            
            # all items in data (as list)
            for idx, item in enumerate(data):
                self.run_cmd("config:system:set", key, str(idx), "--value", item)

        # set config string
        elif key in self.config_value_keys:
            self.run_cmd("config:system:set", key, "--type", "string", "--value", data)

        else:
            raise NextcloudError(f"unknown key: {key}")

    def delete_config(self, key):
        """Deleting config key-value pair completly"""
        self.run_cmd("config:system:delete", key)

    def set_maintenance_on(self):
        """Activating nextcloud maintainance mode"""
        return self.run_cmd("maintenance:mode", "--on")

    def set_maintenance_off(self):
        """Deactivating nextcloud maintainance mode"""
        return self.run_cmd("maintenance:mode", "--off")
    
    def enable_nextbox_app(self):
        """Enable nextbox-app for this nextcloud"""
        out = self.run_cmd("app:enable", "nextbox")
        out = " ".join(out)
        return "already" in out

