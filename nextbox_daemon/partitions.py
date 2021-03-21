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
                    toks = line.split(" ")
                    ## return (mountpoint, fs_type)
                    return toks[1], toks[2]
        return False, False

    def get_parts(self, block_dev, model):
        labels = { path.resolve().name: path.name \
            for path in Path("/dev/disk/by-label/").iterdir() }

        dct = {}
        for path in Path("/dev/disk/by-path/").iterdir():
            part = path.resolve().name
            
            if labels.get(part) in self.hide_labels:
                continue

            if part.startswith(block_dev) and part != block_dev:
                label = labels.get(part)
                mounted, fs_type = self.is_mounted(part)

                real_mounted = "/" if label == self.root_label else mounted
                if real_mounted:
                    data = os.statvfs(real_mounted)
                    free = data.f_bfree * data.f_frsize
                    avail = data.f_blocks * data.f_frsize
                else:
                    avail, free = None, None

                is_special = label in self.special_labels
                
                friendly_name = f"Extra ({model})"
                if real_mounted:
                    friendly_name += f" @ {real_mounted}"
                if is_special:
                    if block_dev.startswith("mm"):
                        friendly_name = f"SD-Card ({label})"
                    else:
                        friendly_name = f"Internal HardDisk ({label})"

                dct[part] = {
                    "name": part,
                    "desc": model,
                    "friendly_name": friendly_name,
                    "label": label,
                    "mounted": real_mounted,
                    "fs": fs_type,
                    "special": is_special,
                    "space":  {"free": free, "avail": avail}
                }
        return dct

    def get_block_device(self, block_dev):
        model = self.get_device_model(block_dev)
        return {
            "name": block_dev, 
            "model": model,
            "parts": self.get_parts(block_dev, model)
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
    def backup_devices(self):
        out = []
        for item in self.block_devices.values():
            for part_name, part_item in item["parts"].items():
                # exlude sd-card & internal harddisk from backups
                if part_item["mounted"] and part_item["mounted"] not in ["/", "/srv"]:
                    path = part_item["mounted"]
                    
                    # only allow unix filesystems for backups for now
                    if part_item["fs"] not in ["btrfs", "ext3", "ext4", "xfs"]:
                        continue
                    
                    out.append({
                        "friendly_name": part_item["friendly_name"],
                        "name": part_name,
                        "path": path,
                        "fs": part_item["fs"]
                    })
        return out

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
    print()
    print(p.backup_devices)