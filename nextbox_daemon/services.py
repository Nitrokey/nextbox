from nextbox_daemon.consts import SYSTEMCTL_BIN
from nextbox_daemon.command_runner import CommandRunner

class Services:

    SAFE_SERVICE_CTRL = ["start", "restart", "status", "is-active"]
    FULL_SERVICE_CTRL = SAFE_SERVICE_CTRL + ["stop", "disable", "enable"]
    
    SERVICES_CTRL = {
        "ddclient": ("ddclient.service", FULL_SERVICE_CTRL),
        "nextbox-daemon": ("nextbox-daemon.service", SAFE_SERVICE_CTRL),
        "nextbox-compse": ("nextbox-compose.service", SAFE_SERVICE_CTRL),
        "reverse-tunnel": ("reverse-tunnel.service", FULL_SERVICE_CTRL)
    }

    def __init__(self):
        ...

    def check(self, name, op):
        return name in self.SERVICES_CTRL \
            and op in self.SERVICES_CTRL[name][1]

    def exec(self, name, op):
        if not self.check(name, op):
            return False

        service, _ = self.SERVICES_CTRL[name]

        cr = CommandRunner([SYSTEMCTL_BIN, op, service], block=True)
        output = [x for x in cr.output if x]
        
        return {
            "service":     name,
            "operation":   op,
            "return-code": cr.returncode,
            "output":      output
        }