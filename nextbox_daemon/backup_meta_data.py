from pathlib import Path
from datetime import datetime
import yaml

from nextbox_daemon.config import log, cfg
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.nextcloud import Nextcloud


class BackupMetaDataException(Exception): pass
class BackupMetaDataFileNotFound(Exception): pass
class BackupDirectoryNotFound(Exception): pass


class BackupMetaData:      
    meta_data_fn = "info.yaml"
    
    marker_fn = "NEXTBOX_BACKUP"
    marker_done_fn = "NEXTBOX_BACKUP.OK"

    sql_dump_fn = "dump.sql"

    components = {
        "data":         "nextcloud/data",
        "apps":         "nextcloud/custom_apps",
        "nextbox":      "nextbox",
        "config":       "nextcloud/config",
        "letsencrypt":  "letsencrypt",
        "sql":          sql_dump_fn,
    }

    latest_version = 2

    rsync_stats_cmd = "/usr/bin/rsync -a --stats {src}"
    rsync_transfer_stats_cmd = "/usr/bin/rsync -a --dry-run --stats {src} {tar}"

    def __init__(self, backup_dir):
        self.nextcloud = Nextcloud()
        self.backup_dir = Path(backup_dir)


        # DEPRECATED - VERSION 1 structure:
        # self.data = {
        #     "state":        "started",
        #     "substate":     "init",
        #     "size_sql":     None,
        #     "size_apps":    None,
        #     "size_data":    None,
        #     "size_nextbox": None,
        #     "started":      str(datetime.now()),
        #     "ended":        None,
        # }

        self.data = {
            "version":      self.latest_version,
            "nc_version":   None,
            "state":        "started",
            "substate":     "init",
            "components": {
                key: {"size": None, "count": None} for key in self.components
            },
            "started": None,
            "ended": None,            
        }

    @property
    def file_path(self):
        return self.backup_dir / self.meta_data_fn

    def get_component_paths(self, root_dir):
        root_dir = root_dir if isinstance(root_dir, Path) else Path(root_dir)
        return {part: (root_dir / path) for part, path in self.components.items()}
        
    def update(self, from_backup_path=None):
        backup_path = self.backup_dir if from_backup_path is None else from_backup_path
                
        if not isinstance(backup_path, Path):
            backup_path = Path(backup_path)
        
        if not backup_path.exists():
            raise BackupDirectoryNotFound(backup_path.as_posix())

        self.data["components"] = self.get_stats(backup_path)
        self.data["nc_version"] = self.nextcloud.get_version()
        self.data["started"] = str(datetime.now())
        self.data["ended"] = None
        self.data["state"] = "started"
        self.data["substate"] = "init"

    def save(self, to_path=None):
        file_path = self.file_path if to_path is None else to_path
        
        if not isinstance(file_path, Path):
            file_path = Path(file_path)

        with file_path.open("w") as fd:
            yaml.dump(self.data, fd)

    def load(self, from_path=None, get_missing=False):      
        file_path = self.file_path if from_path is None else from_path
                
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise BackupMetaDataFileNotFound(file_path.as_posix())

        with file_path.open() as fd:
            loaded = yaml.load(fd)

        version = loaded["version"] if "version" in loaded else 1
        if version == 1:
            self.update_from_version_1(loaded, get_missing)
        else:
            self.data = loaded

    # version 1 is identified due to a non-existing "version"-key
    def update_from_version_1(self, data, get_missing=False):
        self.data["state"] = data["state"]
        self.data["substate"] = data["substate"]
        for key in self.data["components"]:
            self.data["components"][key]["size"] = data.get("size_" + key)
        self.data["started"] = data["started"]
        self.data["ended"] = data["ended"]
    
        # on request update new fields directly
        if get_missing:
            self.data["components"] = self.get_stats(self.backup_dir)
  
            # don't set nextcloud version => cannot find out afterwards
            self.data["nc_version"] = None # Nextcloud().get_version()

    def _parse_rsync_stats(self, raw_stats, no_transfer=True):
        stats = {}
        for line in raw_stats:
            if line.startswith("Number of files:"):
                raw = line.split(":")[1].split("(")[0].replace(",", "").strip()
                stats["count"] = int(raw)
            elif line.startswith("Total file size:"):
                raw = line.split(":")[1].split("b")[0].replace(",", "").strip()
                stats["size"] = int(raw)
            
            if not no_transfer:
                if line.startswith("Total transferred file size:"):
                    raw = line.split(":")[1].split("b")[0].replace(",", "").strip()
                    stats["transfer_size"] = int(raw)
                if line.startswith("Number of regular files transferred:"):
                    raw = line.split(":")[1].replace(",", "").strip()
                    stats["transfer_count"] = int(raw)
        return stats

    def get_stats(self, src_dir, tar_dir=None, strict=True):
        
        if not isinstance(src_dir, Path): 
            src_dir = Path(src_dir)

        # if 'tar_dir' is provided, 'base_dir' is used as 'root_dir'
        if tar_dir is not None and not isinstance(tar_dir, Path):
            tar_dir = Path(tar_dir)

        stats = {}
   
        cmd = self.rsync_stats_cmd if not tar_dir else self.rsync_transfer_stats_cmd

        src_paths = self.get_component_paths(src_dir)
        tar_paths = self.get_component_paths(tar_dir) if tar_dir else {}
        for part in self.components:

            
            src = src_paths[part]
            fmt_dct = {"src": src.as_posix()}

            # for sql
            if not strict and not src.exists():
                continue
            
            if tar_dir:
                # skip entries w/o path
                if tar_paths[part] is None:
                    continue
                tar = tar_paths[part].parent
                fmt_dct["tar"] = tar.as_posix()
                
                # for sql (target sql file won't exist)
                if part == "sql":
                    continue
                    
            cr = CommandRunner(cmd.format(**fmt_dct), block=True)

            raw_stats = []
            found = False
            for line in cr.output:
                if not found and not line.startswith("Number"):
                    continue
                found = True
            
                raw_stats.append(line)

            # parse and save stats
            stats[part] = self._parse_rsync_stats(raw_stats, no_transfer=tar_dir is None)
            
        return stats



        

