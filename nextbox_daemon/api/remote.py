
import urllib.request, urllib.error
import json
import yaml
import requests
from pathlib import Path
from flask import Blueprint, request
import socket 
import ssl
import re
from datetime import datetime as dt

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_queue
from nextbox_daemon.certificates import Certificates
from nextbox_daemon.nextcloud import Nextcloud, NextcloudError
from nextbox_daemon.proxy_tunnel import ProxyTunnel, ProxySetupError
from nextbox_daemon.dns_manager import DNSManager
from nextbox_daemon.status_board import board
from nextbox_daemon.consts import *


from filelock import FileLock

remote_api = Blueprint('remote', __name__)


@remote_api.route("/proxy/register", methods=["POST"])
@requires_auth
def register_proxy():

    # assemble data
    for key in request.form:
        if key == "nk_token":
            token = request.form.get(key)
        elif key == "proxy_domain":
            proxy_domain = request.form.get(key)
            subdomain = proxy_domain.split(".")[0]

    scheme = "https" if cfg["config"]["https_port"] else "http"

    proxy_tunnel = ProxyTunnel()
    try:
        proxy_port = proxy_tunnel.setup(token, subdomain, scheme)
    except ProxySetupError as e:
        cfg["config"]["proxy_active"] = False
        cfg.save()
        log.error(str(e))
        return error(str(e))
    except Exception as e:
        cfg["config"]["proxy_active"] = False
        cfg.save()
        msg = "unexpected error during proxy setup"
        log.error(msg, exc_info=e)
        return error(msg)

    # configure nextcloud
    nc = Nextcloud()
    try:
        nc.set_config("overwriteprotocol", "https")
        nc.set_config("overwritecondaddr", "^172\\.18\\.238\\.1$")
        nc.set_config("trusted_proxies", ["172.18.238.1"])
    except NextcloudError as e:
        cfg["config"]["proxy_active"] = False
        cfg.save()
        msg = "could not configure nextcloud for proxy usage"
        log.error(msg, exc_info=e)
        return error(msg)

    cfg["config"]["proxy_domain"] = proxy_domain
    cfg["config"]["proxy_active"] = True
    cfg["config"]["proxy_port"] = proxy_port
    cfg.save()
    
    # ensure trusted domains are set
    job_queue.put("TrustedDomains")

    return success("Proxy successfully registered")

@remote_api.route("/dyndns/register", methods=["POST"])
@requires_auth
def dyndns_register():
    data = {}
    for key in request.form:
        if key in ["domain", "email"]:
            data[key] = request.form.get(key)
    data["password"] = None

    headers = {"Content-Type": "application/json"}

    req = urllib.request.Request(DYNDNS_DESEC_REGISTER,
        method="POST", data=json.dumps(data).encode("utf-8"), headers=headers)

    try:
        res = urllib.request.urlopen(req).read().decode("utf-8")
    except urllib.error.HTTPError as e:
        desc = e.read()
        return error(f"Could not complete registration", data=json.loads(desc))
    return success(data=json.loads(res))

@remote_api.route("/dyndns/test/ddclient")
@requires_auth
def test_ddclient():
    cr = CommandRunner([DDCLIENT_BIN, "-verbose", "-foreground", "-force"], block=True)
    cr.log_output()

    for line in cr.output:
        if "SUCCESS:" in line:
            return success("DDClient test: OK")
        if "Request was throttled" in line:
            pat = "available in ([0-9]*) seconds"
            try:
                waitfor = int(re.search(pat, line).groups()[0]) + 5
            except:
                waitfor = 10
            return error("DDClient test: Not OK",
                data={"reason": "throttled", "waitfor": waitfor})

    return error("DDClient test: Not OK", data={"reason": "unknown"})


@remote_api.route("/dyndns/test/resolve/ipv6")
@remote_api.route("/dyndns/test/resolve/ipv4")
@requires_auth
def test_resolve4():
    ip_type = request.path.split("/")[-1]
    domain = cfg["config"]["domain"]
    resolve_ip = None
    ext_ip = None

    if not domain:
        return error("no domain is set")

    dns = DNSManager()
    dns.clear_dns_caches()

    if ip_type == "ipv4":
        resolve_ip = dns.resolve_ipv4(domain)
        ext_ip = dns.get_ipv4()
    else:
        resolve_ip = dns.resolve_ipv6(domain)
        ext_ip = dns.get_ipv6()
        
    log.info(f"resolving '{domain}' to IP: {resolve_ip}, external IP: {ext_ip}")
    data = {"ip": ext_ip, "resolve_ip": resolve_ip, "domain": domain}

    # if not both "resolve" and "getip" are successful, we have failed
    if resolve_ip is None or ext_ip is None:
        log.error(f"failed resolving and/or getting external {ip_type}")
        return error("Resolve test: Not OK", data=data)

    # resolving to wrong ip
    if resolve_ip != ext_ip:
        log.warning(f"Resolved {ip_type} does not match external {ip_type}")
        log.warning("This might indicate a bad DynDNS configuration")
        return error("Resolve test: Not OK", data=data)

    # all good!
    return success("Resolve test: OK", data=data)

@remote_api.route("/dyndns/test/reachable")
@requires_auth
def test_http():
    nc = Nextcloud()
    res, req = nc.check_reachability()
    data = yaml.load(res.text)
    data["data"]["ipv4"] = [req["ipv4"], req["domain"]]
    data["data"]["ipv6"] = ["[" + req["ipv6"] + "]" if req["ipv6"] else "", req["domain"]]
    return success(data["msg"][0], data=data["data"])
    
    
@remote_api.route("/dyndns/test/proxy")
@requires_auth
def test_proxy():
    domain = cfg["config"]["proxy_domain"]
    what = "https"
    url = f"{what}://{domain}"
    if not domain:
        return error("no proxy-domain set")
    
    out = {"result": None, "domain": domain}
    try:
        res = requests.get(url, timeout=2)
        out["result"] = True
        out["nextcloud"] = "Nextcloud" in res.text
    except (requests.exceptions.ConnectionError, requests.exceptions.SSLError):
        out["result"] = False
        out["nextcloud"] = False
    
    return success("tested proxy for reachability", data=out)

@remote_api.route("/https")
@requires_auth
def https():
    dct = {
        "domain": cfg.get("config", {}).get("domain"),
        "email": cfg.get("config", {}).get("email"),   
        "https": cfg["config"]["https_port"] is not None,
        "dns_mode": cfg["config"]["dns_mode"]
    }

    return success(data=dct)

@remote_api.route("/https/enable", methods=["POST"])
@requires_auth
def https_enable():

    board.set("tls", {
        "what": "enable",
        "state": "pending",
    })
    job_queue.put("EnableHTTPS")

    return success("HTTPS enabling pending")

@remote_api.route("/https/disable", methods=["POST"])
@requires_auth
def https_disable():
    certs = Certificates()
    if not certs.set_apache_config(ssl=False):
        return error("failed disabling ssl for apache")

    cfg["config"]["https_port"] = None
    cfg.save()

    # we need to "re-wire" the proxy to port 80 on activated TLS
    add_msg = ""
    if cfg["config"]["proxy_active"]:
        subdomain = cfg["config"]["proxy_domain"].split(".")[0]
        scheme = "http"
        token = cfg["config"]["nk_token"]
        proxy_tunnel = ProxyTunnel()
        try:
            proxy_port = proxy_tunnel.setup(token, subdomain, scheme)
        except ProxySetupError as e:
            log.error(exc_info=e)
            add_msg = "(but register at proxy-server error: " + repr(e) + ")"
        except Exception as e:
            log.error(exc_info=e)
            add_msg = "(unexpected error during proxy setup)"

        cfg["config"]["proxy_port"] = proxy_port
        cfg.save()

    return success("HTTPS disabled " + add_msg)


@remote_api.route("/certs")
@requires_auth
def getcerts():
    dct = {
        "cert": None,
    }

    if dct.get("domain"):
        certs = Certificates()
        my_cert = certs.get_cert(dct.get("domain"))
        if my_cert:
            dct["cert"] = my_cert
    
    return success(data=dct)

@remote_api.route("/certs/clear", methods=["POST"])
@requires_auth
def certs_clear():

    if cfg["config"]["https_port"]:
        return error("cannot clear certificates while HTTPS is active")

    certs = Certificates()
    certs.clear_certs()
    
    return success("Cleared all certificates")