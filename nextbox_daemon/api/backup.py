from flask import Blueprint, request

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_queue
from nextbox_daemon.status_board import board
from nextbox_daemon.partitions import Partitions
from nextbox_daemon.raw_backup_restore import RawBackupRestore
from nextbox_daemon.consts import *

backup_api = Blueprint('backup', __name__)

partitions = Partitions()
backup_restore = RawBackupRestore()

@backup_api.route("/backup")
@requires_auth
def backup():
    devs = partitions.backup_devices
    data = {
        "devices": devs,
        "backups": backup_restore.find_backups([dev["path"] for dev in devs]),
        "last_backup": cfg["config"]["last_backup"],
    }

    return success(data=data)

@backup_api.route("/backup/status")
@requires_auth
def backup_status():
    return success(data=board.get("backup_restore"))

@backup_api.route("/backup/status/clear")
@requires_auth
def backup_status_clear():
    board.delete_key("backup_restore")
    return success()

@backup_api.route("/backup/start", methods=["POST"])
@requires_auth
def backup_start():
    tar_path = request.form.get("tar_path")
    found = False
    for dev in partitions.backup_devices:
        if tar_path.startswith(dev["path"]):
            found = dev
            break
    
    if not found:
        msg = "Invalid backup location provided"
        log.error(msg)
        return error(msg)

    log.info(f"Initiating backup onto: {dev['friendly_name']} @ {dev['path']} with target: {tar_path}")

    job_kwargs = {"tar_path": tar_path, "mode": "backup"}
    job_queue.put(("BackupRestore", job_kwargs))

    return success("backup started")


@backup_api.route("/backup/restore", methods=["POST"])
@requires_auth
def restore_start():
    src_path = request.form.get("src_path")
    
    if not backup_restore.check_backup(src_path):
        msg = "Invalid backup, cannot restore"
        log.error(msg)
        return error(msg)

    log.info(f"Initiating restore from: {src_path}")

    job_kwargs = {"tar_path": src_path, "mode": "restore"}
    job_queue.put(("BackupRestore", job_kwargs))

    return success("restore started")
