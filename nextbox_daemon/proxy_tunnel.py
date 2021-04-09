import yaml
import urllib.request, urllib.error
import json

from nextbox_daemon.config import log
from nextbox_daemon.services import Services
from nextbox_daemon.consts import PROXY_REGISTER_URL

from filelock import FileLock


class ProxySetupError(Exception): pass


class ProxyTunnel:
    
    RTUN_CONFIG_PATH = "/srv/nextbox/rtun.yaml"
    RTUN_CONFIG_LOCK_PATH = RTUN_CONFIG_PATH + ".lock"

    def setup(self, token, subdomain, scheme):
        if scheme not in ["http", "https"]:
            raise ProxySetupError(f"provided scheme: {scheme} not 'http' or 'https'")

        local_port = 80 if scheme == "http" else 443
        remote_port = self.register_at_server(token, subdomain, scheme)
        
        self.create_config(token, remote_port, local_port)
        self.start()
        
        log.info("setup proxy:")
        log.info(f"port: {local_port}, remote_port: {remote_port} @ {scheme}")
        
        return remote_port

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
        ctrl.enable("reverse-tunnel")
        ctrl.restart("reverse-tunnel")

    def stop(self):
        ctrl = Services()
        ctrl.disable("reverse-tunnel")
        ctrl.stop("reverse-tunnel")

    def register_at_server(self, token, subdomain, scheme):
        # send register request to proxy-server
        data = {
            "token": token,
            "subdomain": subdomain,
            "scheme": scheme
        }
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(PROXY_REGISTER_URL, 
            data=json.dumps(data).encode("utf-8"), 
            method="POST", headers=headers)
        try:
            res = urllib.request.urlopen(req).read().decode("utf-8")
        except urllib.error.HTTPError as e:
            desc = e.read()
            raise ProxySetupError((f"Could not complete proxy registration", json.loads(desc)))
        
        res = json.loads(res)
        # success return port
        if res["result"] == "success":
            return res["data"]["port"]

        # on fail, raise with error-msg
        err_msg = res["msg"][0] if isinstance(res["msg"], (list, tuple)) else res["msg"]
        raise ProxySetupError(err_msg)
        
        