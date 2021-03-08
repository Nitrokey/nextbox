from pathlib import Path
import os

from nextbox_daemon.config import log
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.consts import *


class Partitions:
    exclude_devs = ["ram", "loop"]
    special_labels = ["rootfs", "boot", "NextBoxHardDisk"]
    hide_labels = ["boot"]
    root_label = "rootfs"
    backup_mountpoint = "/media/backup"

    def __init__(self):
        pass

    def get_device_model(self, block_dev):
        try:
            model = (Path("/sys/block") / block_dev / "device/model") \
                .read_text("utf-8").strip()
            vendor = (Path("/sys/block") / block_dev / "device/vendor") \
                .read_text("utf-8").strip()
            return model + " " + vendor
        except FileNotFoundError:
            return "n/a"
        except Exception as e:
            log.error("could not get device model", exc_info=e)
            return None


    def is_mounted(self, part):
        with Path("/proc/mounts").open() as fd:
            for line in fd:
                if not line.startswith("/"):
                    continue
                if line.startswith(f"/dev/{part}"):
                    return line.split(" ", 2)[1]
        return False

    def get_parts(self, block_dev):
        labels = { path.resolve().name: path.name \
            for path in Path("/dev/disk/by-label/").iterdir() }

        dct = {}
        for path in Path("/dev/disk/by-path/").iterdir():
            part = path.resolve().name
            
            if labels.get(part) in self.hide_labels:
                continue

            if part.startswith(block_dev) and part != block_dev:
                label = labels.get(part)
                mounted = self.is_mounted(part)

                real_mounted = "/" if label == self.root_label else mounted
                if real_mounted:
                    data = os.statvfs(real_mounted)
                    free = data.f_bfree * data.f_frsize
                    avail = data.f_blocks * data.f_frsize
                else:
                    avail, free = None, None

                dct[part] = {
                    "name": part,
                    "label": label,
                    "mounted": real_mounted,
                    "special": label in self.special_labels,
                    "backup": mounted == self.backup_mountpoint,
                    "space":  {"free": free, "avail": avail}
                }
        return dct

    def get_block_device(self, block_dev):
        return {
            "name": block_dev, 
            "model": self.get_device_model(block_dev),
            "parts": self.get_parts(block_dev)
        }


    def mount_partition(self, mount_device, mount_target):
        cr = CommandRunner([MOUNT_BIN, mount_device, mount_target], block=True)
        if cr.returncode == 0:
            return True
        else:
            cr.log_output()
            return False

    def umount_partition(self, mount_target):
        cr = CommandRunner([UMOUNT_BIN, mount_target], block=True)
        if cr.returncode == 0:
            return True
        else:
            cr.log_output()
            return False

    @property
    def mounted(self):
        dct = {}
        for dev in self.block_devices.values():
            for part in dev["parts"].values():
                if part["mounted"]:
                    dct[part["mounted"]] = part["name"]
        return dct 

    @property
    def block_devices(self):
        dct = {}
        for dev in Path("/sys/block").iterdir():
            if any(dev.name.startswith(ex) for ex in self.exclude_devs):
                continue
            dct[dev.name] = self.get_block_device(dev.name)
        return dct





if __name__ == "__main__":
    p = Partitions()
    print(p.block_devices)