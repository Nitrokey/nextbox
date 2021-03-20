import yaml


from nextbox_daemon.config import log
from nextbox_daemon.services import Services

from filelock import FileLock


class ProxyTunnel:
    
    RTUN_CONFIG_PATH = "/srv/nextbox/rtun.yaml"
    RTUN_CONFIG_LOCK_PATH = RTUN_CONFIG_PATH + ".lock"

    def create_config(self, token, remote_port, local_port):
        # configure reverse-tunnel
        rtun_conf = {
            "gateway_url": "wss://nextbox.link", 
            "auth_key": token, 
            "forwards": [{
                "port": f"{remote_port}/tcp", 
                "destination": f"127.0.0.1:{local_port}"
            }]
        }
        
        # actually write config
        with FileLock(self.RTUN_CONFIG_LOCK_PATH, timeout=10):
            with open(self.RTUN_CONFIG_PATH, "w") as fd:
                yaml.dump(rtun_conf, fd)
        
    def start(self):
        ctrl = Services()
        ctrl.exec("reverse-tunnel", "enable")
        ctrl.exec("reverse-tunnel", "restart")

    def stop(self):
        ctrl = Services()
        ctrl.exec("reverse-tunnel", "disable")
        ctrl.exec("reverse-tunnel", "stop")