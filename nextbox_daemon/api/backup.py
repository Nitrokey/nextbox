from flask import Blueprint, request

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.utils import requires_auth, success, error, check_for_backup_process
from nextbox_daemon.config import cfg, log
from nextbox_daemon.consts import *

backup_api = Blueprint('backup', __name__)



@backup_api.route("/backup")
@requires_auth
def backup():
    data = dict(cfg["config"])
    #data["operation"] = check_for_backup_process()
    data["found"] = []

    if get_partitions()["backup"] is not None:
        for name in os.listdir("/media/backup"):
            p = Path("/media/backup") / name
            try:
                size =  (p / "size").open().read().strip().split()[0]
            except FileNotFoundError:
                continue

            data["found"].append({
                "name": name,
                "created": p.stat().st_ctime,
                "size": size
            })
            data["found"].sort(key=lambda x: x["created"], reverse=True)

    return success(data=data)


#@app.route("/backup/cancel")
#def backup_cancel(name):
#    global backup_proc
#
#    subprocess.check_call(["killall", "nextcloud-nextbox.export"])
#    #subprocess.check_call(["killall", "nextcloud-nextbox.import"])
#
#    pass


@backup_api.route("/backup/start")
@requires_auth
def backup_start():
    global backup_proc
    backup_info = check_for_backup_process()
    parts = get_partitions()

    if backup_info["running"]:
        return error("backup/restore operation already running", data=backup_info)

    if not parts["backup"]:
        return error("no 'backup' storage mounted")

    backup_proc = CommandRunner([BACKUP_EXPORT_BIN],
        cb_parse=parse_backup_line, block=False)
    backup_proc.user_info = "backup"

    return success("backup started", data=backup_info)


@backup_api.route("/backup/restore/<name>")
@requires_auth
def backup_restore(name):
    global backup_proc
    backup_info = check_for_backup_process()

    if ".." in name or "/" in name:
        return error("invalid name", data=backup_info)

    if backup_info["running"]:
        return error("backup/restore operation already running", data=backup_info)

    directory = f"/media/backup/{name}"
    backup_proc = CommandRunner([BACKUP_IMPORT_BIN, directory],
        cb_parse=parse_backup_line, block=False)
    backup_proc.user_info = "restore"

    return success("restore started", data=backup_info)
