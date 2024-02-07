import os
import shutil
from pathlib import Path
from zipfile import ZipFile
from base64 import b64encode

from flask import Blueprint, request


from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error, tail, local_ip, nextbox_version
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_queue
from nextbox_daemon.services import services
from nextbox_daemon.proxy_tunnel import ProxyTunnel
from nextbox_daemon.status_board import board
from nextbox_daemon.dns_manager import DNSManager
from nextbox_daemon.consts import *

generic_api = Blueprint('generic', __name__)



@generic_api.route("/status")
@requires_auth
def get_status():
    # add pkginfo if not yet inside status-board
    if not board.contains_key("pkginfo"):
        board.set("pkginfo", {"version": nextbox_version()})
        keys = board.get_keys()

    # update ips, not more often than 1min
    if board.is_older_than("ips", 60):
        dns = DNSManager()
        board.set("ips", {"ipv4": dns.get_ipv4(), "ipv6": dns.get_ipv6()})

    # return all board data
    keys = board.get_keys()
    status_data = {key: board.get(key) for key in keys}
    
    return success(data=status_data)

@generic_api.route("/log")
@generic_api.route("/log/<num_lines>")
@requires_auth
def show_log(num_lines=50):
    ret = tail(LOG_FILENAME, num_lines)
    return error(f"could not read log: {LOG_FILENAME}") if ret is None \
        else success(data=ret[:-1])


@generic_api.route("/system", methods=["POST", "GET"])
@requires_auth
def system_settings():
    if request.method == "GET":
        return success(data={
            "log_lvl": cfg["config"]["log_lvl"],
            "expert_mode": cfg["config"]["expert_mode"]
        })

    elif request.method == "POST":
        pass


@generic_api.route("/logs")
@requires_auth
def get_logs():
    
    log_dir = Path("/srv/logdump")
    
    journal_logs = {
        "nextbox-daemon": "journald.nextbox-daemon.log", 
        "nextbox-compose": "journald.nextbox-compose.log"
    }
    cmd_dump_journalctl = "journalctl --no-pager -n 1000 -xeu {daemon} > {log_dir}/{filename}"
    
    var_logfiles = [
        "/var/log/dpkg.log", 
        "/var/log/unattended-upgrades/unattended-upgrades.log", 
        "/var/log/unattended-upgrades/unattended-upgrades-dpkg.log", 
        "/var/log/unattended-upgrades/unattended-upgrades-shutdown.log", 
        "/var/log/kern.log",
        "/var/log/letsencrypt/letsencrypt.log",
        LOG_FILENAME
    ]
    
    logfiles = []

    # cleanup logdump dir
    shutil.rmtree(log_dir.as_posix())
    os.makedirs(log_dir.as_posix())

    for unit, fn in journal_logs.items():
        cmd = cmd_dump_journalctl.format(daemon=unit, filename=fn, log_dir=log_dir)
        CommandRunner(cmd, block=True, shell=True)
        logfiles.append(log_dir / fn)
        
    for path in var_logfiles:
        if Path(path).exists():
            shutil.copy(path, log_dir.as_posix())
            logfiles.append(log_dir / Path(path).name)
    
    hash_file = Path(log_dir) / "sha256.txt"
    CommandRunner(f"sha256sum {log_dir.as_posix()}/* > {hash_file.as_posix()}", shell=True, block=True)
    logfiles.append(hash_file)

    zip_path = "/srv/nextbox-logs.zip"
    with ZipFile(zip_path, "w") as fd:
        for path in logfiles:
            fd.write(path, path.name)
    
    with open(zip_path, "rb") as fd:
        return success(data={"zip": b64encode(fd.read())})


@generic_api.route("/ssh", methods=["POST", "GET"])
@requires_auth
def ssh_set():
    auth_p_dir = Path("/home/nextuser/.ssh")
    if not auth_p_dir.exists():
        os.makedirs(auth_p_dir.as_posix())

    auth_p = auth_p_dir / "authorized_keys"
    
    if request.method == "GET":
        ip = local_ip()
        if not auth_p.exists():
            return success(data={
                "pubkey": "",
                "local_ip": ip
            })
        with auth_p.open() as fd:
            return success(data={
                "pubkey": fd.read(),
                "local_ip": ip
            })      

    elif request.method == "POST":
        pubkey = request.form.get("pubkey")
        
        with auth_p.open("w") as fd:
            fd.write(pubkey.strip() + "\n")
        
        log.info(f"setting ssh pub key: {pubkey}")
        return success()



@generic_api.route("/reboot", methods=["POST"])
@requires_auth
def reboot():
    log.info("REBOOTING NOW - by /reboot request")
    cr = CommandRunner("reboot")
    if cr.returncode != 0:
        return error("failed executing: 'reboot'")
    return success(data={})

@generic_api.route("/poweroff", methods=["POST"])
@requires_auth
def poweroff():
    log.info("POWER-OFF - by /poweroff request")
    cr = CommandRunner("poweroff")
    if cr.returncode != 0:
        return error("failed executing: 'poweroff'")
    return success(data={})


@generic_api.route("/debianVersion", methods=["GET"])
@requires_auth
def debianVersion():
    log.info("debianVersion - by /debianVersion request")
    version_file = Path("/etc/debian_version")
    with version_file.open() as fd:
        version = fd.read()
    return success(data={"version": int(version.split(".")[0])})


@generic_api.route("/updateDebian", methods=["POST"])
@requires_auth
def updateDebian():
    log.info("updateDebian - by /updateDebian    request")
    cr = CommandRunner("nohup /usr/bin/nextbox-update-debian.sh")
    if cr.returncode != 0:
        return error("failed executing: 'updateDebian'")
    return success(data={})



@generic_api.route("/service/<name>/<operation>")
@requires_auth
def service_operation(name, operation):
    if not services.check(name, operation):
        return error("not allowed")
        
    dct = services.exec(name, operation)
    return success(data=dct)
    

@generic_api.route("/config", methods=["POST", "GET"])
@requires_auth
def handle_config():
    if request.method == "GET":
        data = dict(cfg["config"])
        try:
            data["conf"] = Path(DDCLIENT_CONFIG_PATH).read_text("utf-8")
        except FileNotFoundError:
            data["conf"] = ""
        return success(data=data)

    # save dyndns related values to configuration
    elif request.method == "POST":
        run_jobs = []
        for key in request.form:
            val = request.form.get(key)

            # special config-value 'conf' represents ddclient-config-contents
            if key == "conf":
                old_conf = Path(DDCLIENT_CONFIG_PATH).read_text("utf-8")
                if old_conf != val:
                    log.info("writing ddclient config and restarting service")
                    Path(DDCLIENT_CONFIG_PATH).write_text(val, "utf-8")
                    
                elif len(val.strip()) == 0:
                    log.info("writing empty ddclient config")
                    Path(DDCLIENT_CONFIG_PATH).write_text(val, "utf-8")
                    services.stop("ddclient")
                    services.disable("ddclient")
                    
                if len(val.strip()) > 0:
                    services.enable("ddclient")
                    services.restart("ddclient")

                run_jobs.append("DynDNSUpdate")


            elif key in AVAIL_CONFIGS and val is not None:
                # only allow valid DYNDNS_MODES
                if key == "dns_mode" and val not in DYNDNS_MODES:
                    log.warning(f"key: 'dns_mode' has invalid value: {val} - skipping")
                    continue
                
                # start DynDNS update on "desec_done"
                elif key == "dns_mode" and val == "desec_done":
                    run_jobs.append("DynDNSUpdate")

                # start TrustedDomains update on new domain
                elif "domain" in key:
                    run_jobs.append("TrustedDomains")

                # deactivate proxy on request
                elif key == "proxy_active" and val.lower() == "false":
                    proxy_tunnel = ProxyTunnel()
                    proxy_tunnel.stop()

                # skip if 'val' is empty
                elif val is None:
                    log.debug(f"skipping key: '{key}' -> no value provided")
                    continue

                # convert to bool, ugly?
                if val.lower() in ["true", "false"]:
                    val = val.lower() == "true"

                # put key-value into cfg and save (yes, saving each value)
                cfg["config"][key] = val
                log.debug(f"saving key: '{key}' with value: '{val}'")
                cfg.save()

        # run jobs collected during configuration update
        if len(run_jobs) > 0:
            for job in run_jobs:
                job_queue.put(job)

        return success("DynDNS configuration saved")
