from pathlib import Path

from flask import Blueprint, request


from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error, tail
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_queue
from nextbox_daemon.consts import *

generic_api = Blueprint('generic', __name__)



@generic_api.route("/overview")
def show_overview():
    return success(data={
        "storage": get_partitions(),
        "backup": check_for_backup_process()
    })


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





@generic_api.route("/service/<name>/<operation>")
@requires_auth
def service_operation(name, operation):
    if name not in ["ddclient", "nextbox-daemon", "nextbox-compose"]:
        return error("not allowed")
    if operation not in ["start", "restart", "status", "is-active"]:
        return error("not allowed")

    if name == "ddclient":
        cr = CommandRunner([SYSTEMCTL_BIN, operation, DDCLIENT_SERVICE], block=True)
    elif name == "nextbox-daemon":
        cr = CommandRunner([SYSTEMCTL_BIN, operation, NEXTBOX_SERVICE], block=True)
    elif name == "nextbox-compose":
        cr = CommandRunner([SYSTEMCTL_BIN, operation, COMPOSE_SERVICE], block=True)
    else:
        return error("not allowed")

    output = [x for x in cr.output if x]
    return success(data={
        "service":     name,
        "operation":   operation,
        "return-code": cr.returncode,
        "output":      output
    })


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
                    run_jobs.append("ProxySSH")

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