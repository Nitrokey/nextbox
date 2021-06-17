from nextbox_daemon.config import log
from nextbox_daemon.consts import SYSTEMCTL_BIN
from nextbox_daemon.command_runner import CommandRunner

class Services:
    """
    SystemD service/unit handling class

    The `systemctl` execution is blocking and not checked for errors, returning
    all (merged stdout/stderr) results as `output` with its `return-code`.

    * allows certain set of services to be controlled (`SERVICES_CTRL`)
    * services control is either: `SAFE_SERVICE_CTRL` or `FULL_SERVICE_CTRL`
      restricts most services to: 'start', 'restart', 'status', 'is-active'
    """

    SAFE_SERVICE_CTRL = ["start", "restart", "status", "is-active", "unmask"]
    FULL_SERVICE_CTRL = SAFE_SERVICE_CTRL + ["stop", "disable", "enable"]
    
    SERVICES_CTRL = {
        "ddclient": ("ddclient.service", FULL_SERVICE_CTRL),

        "nextbox-daemon": ("nextbox-daemon.service", SAFE_SERVICE_CTRL),
        "nextbox-compose": ("nextbox-compose.service", FULL_SERVICE_CTRL),
        "nextbox-updater": ("nextbox-updater.service", SAFE_SERVICE_CTRL),
        "nextbox-factory-reset": ("nextbox-factory-reset.service", SAFE_SERVICE_CTRL),

        "reverse-tunnel": ("reverse-tunnel.service", FULL_SERVICE_CTRL),
        "apt-daily": ("apt-daily.service", SAFE_SERVICE_CTRL),
        "apt-daily-upgrade": ("apt-daily-upgrade.service", SAFE_SERVICE_CTRL),
    }

    # shortcut methods
    def status(self, name): return self.exec(name, "status")
    def is_active(self, name): return self.exec(name, "is-active")
    def start(self, name): return self.exec(name, "start")
    def stop(self, name): return self.exec(name, "stop")
    def restart(self, name): return self.exec(name, "restart")
    def enable(self, name): return self.exec(name, "enable")
    def disable(self, name): return self.exec(name, "disable")
    def unmask(self, name): return self.exec(name, "unmask")

    def check(self, name, op):
        """Check, if given service (name) is allowed to run op(eration)"""

        return name in self.SERVICES_CTRL \
            and op in self.SERVICES_CTRL[name][1]

    def exec(self, name, op):
        """Execute 'op(eration)' on service identified with 'name'"""

        # check if operation (op) is allowed for this service (name)
        if not self.check(name, op):
            log.error(f"failed check at exec, service: {name} operation: {op}")
            return False

        # get full service name (including arg if applicable)
        service, _ = self.SERVICES_CTRL[name]

        # run 'systemctl' command
        cr = CommandRunner([SYSTEMCTL_BIN, op, service], block=True)
        output = [x for x in cr.output if x]
        
        return {
            "service":     name,
            "operation":   op,
            "return-code": cr.returncode,
            "output":      output
        }

services = Services()