import os
import shutil
from pathlib import Path
from zipfile import ZipFile
from base64 import b64encode

from flask import Blueprint, request, send_file


from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error, tail
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_queue
from nextbox_daemon.services import Services
from nextbox_daemon.status_board import board
from nextbox_daemon.consts import *

generic_api = Blueprint('generic', __name__)



@generic_api.route("/status")
def show_overview():
    keys = board.get_keys()

    if "pkginfo" not in keys:
        job_queue.put("GenericStatusUpdate")

    out = {}
    for key in keys:
        out[key] = board.get(key)
    return success(data=out)


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


#
# @app.route("/token/<token>/<allow_ip>")
# def set_token(token, allow_ip):
#
#     if request.remote_addr != "127.0.0.1":
#         #abort(403)
#         return error("not allowed")
#
#     cfg["token"]["value"] = token
#     cfg["token"]["created"] = time.time()
#     cfg["token"]["ip"] = allow_ip
#     save_config(cfg, CONFIG_PATH)
#
#     return success()




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
        
        #print("")
    
    for path in var_logfiles:
        shutil.copy(path, log_dir.as_posix())
        logfiles.append(log_dir / Path(path).name)
    
    hash_file = Path(log_dir) / "sha256.txt"
    CommandRunner(f"sha256sum {log_dir.as_posix()}/* > {hash_file.as_posix()}", shell=True, block=True)
    logfiles.append(hash_file)

    print(logfiles)

    zip_path = "/srv/nextbox-logs.zip"
    with ZipFile(zip_path, "w") as fd:
        for path in logfiles:
            fd.write(path, path.name)
    
    with open(zip_path, "rb") as fd:
        return success(data={"zip": b64encode(fd.read())})
    #send_file(zip_path, mimetype="application/zip",  as_attachment=True, attachment_filename=zip_path)
    

@generic_api.route("/ssh", methods=["POST", "GET"])
@requires_auth
def ssh_set():
    auth_p_dir = Path("/home/nextuser/.ssh")
    if not auth_p_dir.exists():
        os.makedirs(auth_p_dir.as_posix())

    auth_p = auth_p_dir / "authorized_keys"
    
    if request.method == "GET":
        if not auth_p.exists():
            return success(data={
                "pubkey": "",
            })
        with auth_p.open() as fd:
            return success(data={
                "pubkey": fd.read()
            })      

    elif request.method == "POST":
        pubkey = request.form.get("pubkey")
        
        with auth_p.open("w") as fd:
            fd.write(pubkey.strip() + "\n")
        
        log.info(f"setting ssh pub key: {pubkey}")
        return success()



@generic_api.route("/service/<name>/<operation>")
@requires_auth
def service_operation(name, operation):
    ctrl = Services()
    if not ctrl.check(name, operation):
        return error("not allowed")
        
    dct = ctrl.exec(name, operation)
    return success(data=dct)
    

@generic_api.route("/config", methods=["POST", "GET"])
@requires_auth
def handle_config():
    if request.method == "GET":
        data = dict(cfg["config"])
        try:
            data["conf"] = Path(DDCLIENT_CONFIG_PATH).read_text("utf-8").split("\n")
        except FileNotFoundError as e:
            data["conf"] = ""
        return success(data=data)

    # save dyndns related values to configuration
    elif request.method == "POST":
        run_jobs = []
        for key in request.form:
            val = request.form.get(key)
            if key == "conf":
                old_conf = Path(DDCLIENT_CONFIG_PATH).read_text("utf-8")
                if old_conf != val:
                    log.info("writing ddclient config and restarting service")
                    Path(DDCLIENT_CONFIG_PATH).write_text(val, "utf-8")
                    service_operation("ddclient", "restart")

            elif key in AVAIL_CONFIGS and val is not None:
                if key == "dns_mode" and val not in DYNDNS_MODES:
                    log.warning(f"key: 'dns_mode' has invalid value: {val} - skipping")
                    continue
                
                elif "domain" in key:
                    run_jobs.append("TrustedDomains")

                elif key == "proxy_active" and val.lower() == "false":
                    #run_jobs.append("ProxySSH")
                    service_operation("reverse-tunnel", "stop")
                    service_operation("reverse-tunnel", "disable")


                elif val is None:
                    log.debug(f"skipping key: '{key}' -> no value provided")
                    continue

                if val.lower() in ["true", "false"]:
                    val = val.lower() == "true"

                cfg["config"][key] = val
                log.debug(f"saving key: '{key}' with value: '{val}'")
                cfg.save()

        if len(run_jobs) > 0:
            for job in run_jobs:
                job_queue.put(job)

        return success("DynDNS configuration saved")