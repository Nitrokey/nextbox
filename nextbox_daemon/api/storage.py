from flask import Blueprint
from pathlib import Path
import os

from nextbox_daemon.utils import requires_auth, success, error, get_partitions
from nextbox_daemon.config import cfg, log
from nextbox_daemon.partitions import Partitions
from nextbox_daemon.consts import *

storage_api = Blueprint('storage', __name__)

partitions = Partitions()

@storage_api.route("/storage")
@requires_auth
def storage():
    return success(data=partitions.block_devices)


@storage_api.route("/storage/mount/<device>")
@storage_api.route("/storage/mount/<device>/<name>")
@requires_auth
def mount_storage(device, name=None):  
    devs = partitions.block_devices
    mounted = partitions.mounted
    
    found = False
    for dev in devs.values():
        for part in dev["parts"].values():
            if part["name"] == device:
                found = True
                if part["mounted"]:
                    return error("device already mounted")
                if part["special"]:
                    return error("cannot mount special device")

    if not found:
        return error("Could not find device!")

    if name is None:
        for idx in range(1, 11):
            _name = f"extra-{idx}"
            mount_target = f"/media/{_name}"
            if mount_target not in mounted:
                name = _name
                break

        if name is None:
            return error("cannot determine mount target, too many mounts?")

    if ".." in device or "/" in device:
        return error("invalid device")
    if ".." in name or "/" in name:
        return error("invalid name")

    mount_target = f"/media/{name}"
    mount_device = f"/dev/{device}"
    
    if not os.path.exists(mount_target):
        os.makedirs(mount_target)

    if partitions.mount_partition(mount_device, mount_target):
        return success("Mounting successful")
    else:
        return error("Failed mounting, check logs...")


@storage_api.route("/storage/umount/<name>")
@requires_auth
def umount_storage(name):
    if ".." in name or "/" in name:
        return error("invalid name")

    mount_target = f"/media/{name}"

    if mount_target not in partitions.mounted:
        return error("not mounted")

    if partitions.umount_partition(mount_target):
        return success("Unmounting successful")
    else:
        return error("Failed unmount, check logs...")



