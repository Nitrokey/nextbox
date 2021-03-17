import yaml
import os
from pathlib import Path
from datetime import datetime
from filelock import FileLock
import shutil


from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.nextcloud import Nextcloud
from nextbox_daemon.config import log

class RawBackupRestore:
    dirs = {
        "data":         "/srv/nextcloud/data",
        "apps":         "/srv/nextcloud/custom_apps",
        "nextbox":      "/srv/nextbox",
        "config":       "/srv/nextcloud/config",
        "letsencrypt":  "/etc/letsencrypt",
    }
    db_env = "/srv/nextbox/docker.env"
    sql_dump_fn = "dump.sql"

    db_export_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysqldump nextcloud -u root --lock-tables --password={pwd} > {path}"
    db_import_cmd = "/usr/bin/docker exec -i nextbox-compose_db_1 /usr/bin/mysql nextcloud -u root --password={pwd} < {path}"
    db_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysql -u root --password={pwd} -e '{sql}'"
    
    rsync_base_cmd = "/usr/bin/rsync --delete -av {src} {tar}"
    rsync_stats_cmd = "/usr/bin/rsync -a --dry-run --stats {src} {tar}"

    def __init__(self):
        self.nc = Nextcloud()

        self.rsync_proc = None
        self.rsync_stats = {}
        self.activity_desc = None
    
    ### rsync-dry run parsed output
    # Number of files: 6,376 (reg: 5,272, dir: 1,104)
    # Number of created files: 0
    # Number of deleted files: 0
    # Number of regular files transferred: 0
    # Total file size: 123,412,32

    def rsync_dir(self, key, src_dir, tar_dir):
        """
        rsync is used to copy files for export & import.
        * a --dry-run is parsed 1st to determine the number of files (paths) to be created on the target side 
        * -av is used to get one line of output for each "created" file (path), which determines the percentage
        """
        cmd = self.rsync_stats_cmd.format(src=src_dir, tar=tar_dir)
        cr = CommandRunner(cmd, block=True)
        stats = {"key": key}
        parsing = {
            "Number of files:":                     "all",
            "Number of created files:":             "create",
            "Number of deleted files:":             "delete",
            "Number of regular files transferred:": "transfer",
            "Total file size:":                     "size"
        }
        for line in cr.output:
            for needle, tag in parsing.items():
                if needle in line:
                    try:
                        num_tok = line.split(":")[1].strip().split(" ")[0].strip()
                        stats[tag] = int(num_tok.replace(",", ""))
                    except ValueError:
                        log.warning(f"failed parsing: {tag} - line: {line}")
                    break

            # all what we need is parsed
            if len(stats) >= 6:
                break
        self.rsync_stats = stats
        
        def parse(line, data_dct):
            data_dct.setdefault("line", 0)
            data_dct.setdefault("ratio", 0)
            data_dct["num_files"] = stats
            data_dct["line"] += 1

            cnt = stats.get("create", 0)
            if cnt == 0:
                data_dct["ratio"] = 100
            else:
                data_dct["ratio"] = int(round(min(1, max(0, data_dct["line"] / cnt)), 2) * 100)

        cmd = self.rsync_base_cmd.format(src=src_dir, tar=tar_dir)
        self.rsync_proc = CommandRunner(cmd, cb_parse=parse, block=False)
        return False

    ###
    ### check and output import/export progress 
    ###
    def check_progress(self):
        if self.activity_desc:
            if self.rsync_proc:
                # only evaluate returncode, if we've finished execution
                if not self.rsync_proc.running:
                    # all went fine
                    if self.rsync_proc.returncode == 0:
                        self.rsync_proc = None
                        out = "finished", self.activity_desc, 100
                        self.activity_desc = None
                        return out
                    # failed!
                    if self.rsync_proc.returncode != 0:
                        self.rsync_proc = None
                        out = "failed", self.activity_desc, 100
                        self.activity_desc = None
                        return out
                # otherwise, just check for `.parsed` and return parsed-state
                if self.rsync_proc.parsed:
                    return "active", self.activity_desc, self.rsync_proc.parsed.get("ratio", 0)
                
        return "inactive", self.activity_desc, 0

    ###
    ### parts' export/import 
    ###
    def export_dir(self, key, tar_dir):
        self.activity_desc = (key, "export")
        self.rsync_dir(key, self.dirs[key], tar_dir)
        log.info(f"starting {key} export")
        if self.rsync_stats:
            self.update_meta(tar_dir, {"size_" + key: self.rsync_stats.get("size", 0)})
        
    def import_dir(self, key, src_dir):
        self.activity_desc = (key, "import")
        src_dir = Path(src_dir)
        key_path = Path(self.dirs[key])
        src_path = src_dir / key_path.name
        tar_path = key_path.parent
        self.rsync_dir("data", src_path.as_posix(), tar_path.as_posix())
        log.info(f"starting {key} import")
        
    def get_sql_password(self):
        with Path(self.db_env).open() as fd:
            for line in fd:
                if "MYSQL_ROOT_PASSWORD" in line:
                    _, val = line.split("=", 1)
                    return val.strip()

    def export_sql(self, tar_path):
        pwd = self.get_sql_password()
        if pwd is None:
            log.error("cannot get sql password for export, aborting...")
            return False
        
        self.nc.set_maintenance_on()

        tar_sql_path = Path(tar_path) / self.sql_dump_fn
        cmd = self.db_export_cmd.format(pwd=pwd, path=tar_sql_path.as_posix())
        cr = CommandRunner(cmd, block=True, shell=True)
        
        self.nc.set_maintenance_off()

        upd = {"size_sql": os.path.getsize(tar_sql_path.as_posix())}
        self.update_meta(tar_path, upd)

        return cr.returncode == 0

    def import_sql(self, src_path):
        pwd = self.get_sql_password()
        if pwd is None:
            log.error("cannot get sql password for import, aborting...")
            return False

        src_sql_path = Path(src_path) / self.sql_dump_fn
        if not src_sql_path.exists():
            log.error("sql-import data path not found, aborting...")
            return False

        self.nc.set_maintenance_on()
        
        # drop database
        cmd = self.db_cmd.format(pwd=pwd, sql="DROP DATABASE nextcloud")
        cr = CommandRunner(cmd, block=True)

        # create new database
        cmd = self.db_cmd.format(pwd=pwd, sql="CREATE DATABASE nextcloud")
        cr = CommandRunner(cmd, block=True)

        # grant 'nextcloud' permissions to user: 'nextcloud'
        cmd = self.db_cmd.format(pwd=pwd, sql="GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost'")
        cr = CommandRunner(cmd, block=True)

        # import sql-dump
        cmd = self.db_import_cmd.format(pwd=pwd, path=src_sql_path.as_posix())
        cr = CommandRunner(cmd, block=True, shell=True)
        
        self.nc.set_maintenance_off()

        return cr.returncode == 0

    ###
    ### meta data handling
    ###
    def start_meta(self, tar_path):
        """
            Init meta-file: `info.yaml` inside the backup directory
            Touch `NEXTBOX_BACKUP` inside target dir to mark as a backup
        """
        info = {
            "state":        "started",
            "substate":     "init",
            "size_sql":     None,
            "size_apps":    None,
            "size_data":    None,
            "size_nextbox": None,
            "started":      str(datetime.now()),
            "ended":        None,
        }
        self.write_meta(tar_path, info)

        # touch file inside backup-dir - to flag: we are are backup
        nextbox_mark  = Path(tar_path) / "NEXTBOX_BACKUP"
        with open(nextbox_mark, "w") as fd:
            fd.write("")

    def end_meta(self, tar_path):
        """
            Finalize meta-file: `info.yaml` inside the backup directory
            Touch `NEXTBOX_BACKUP.OK` in addition to mark a proper backup    
        """
        upd = {
            "state":    "finished", 
            "substate": None, 
            "ended":    str(datetime.now())
        }
        self.update_meta(tar_path, upd)

        # touch file inside backup-dir - to flag: we are done
        nextbox_mark  = Path(tar_path) / "NEXTBOX_BACKUP.OK"
        with open(nextbox_mark, "w") as fd:
            fd.write("")
        
    def update_meta(self, tar_path, update):
        """Update meta-data-dict using `update` (dct)"""
        info = self.read_meta(tar_path)
        info.update(update)    
        self.write_meta(tar_path, info)

    def read_meta(self, tar_path):
        """Read and return meta-data-dict"""
        tar_meta_path = Path(tar_path) / "info.yaml"
        with open(tar_meta_path, "r") as fd:
            info = yaml.load(fd)
        return info

    def write_meta(self, tar_path, info):
        """Write `info` as meta-data-dict to file"""
        tar_meta_path = Path(tar_path) / "info.yaml"
        with open(tar_meta_path, "w") as fd:
            yaml.dump(info, fd)

    def check_backup(self, src_path):
        """Check `path` for a valid backup"""
        
        path = Path(src_path)
        
        # check for flag file
        if not (path / "NEXTBOX_BACKUP.OK").exists():
            log.error(f"restore cancel - {src_path}: 'NEXTBOX_BACKUP.OK' missing")
            return False
        
        # read meta info file
        try:
            info = self.read_meta(src_path)
        except FileNotFoundError:
            log.error(f"restore cancel - {src_path}: meta-info not found")
            return False
        
        # check for correct state
        if info["state"] != "finished":
            log.error(f"restore cancel - {src_path}: meta-info state not 'finished'")
            return False

        # check for all sizes > 0 and src_dirs (+sql-dump) exist in backup
        for key, val in info.items():
            if key.startswith("size_"):
                _, what = key.split("_")
                # check meta-size > 0
                if not val > 0:
                    log.error(f"restore cancel - {src_path}: size for '{what}'' not > 0")
                    return False
                # check existance of dir
                if what != "sql":
                    p = src_path / Path(self.dirs[what]).name
                    if not p.exists():
                        log.error(f"restore cancel - {src_path}: {p} not found for restoring: {what}")
                        return False
                # or sql dump file
                else:
                    p = src_path / self.sql_dump_fn
                    if not p.exists():
                        log.error(f"restore cancel - {src_path}: {p} not found for db-restore")
                        return False
        return True

    
    ###
    ### convinience, yield-based full-export (use with StopIteration)
    ###
    def full_export(self, tar_path):
        steps = [
            ("sql",         lambda: self.export_sql(tar_path)),
            ("data",        lambda: self.export_dir("data", tar_path)), 
            ("apps",        lambda: self.export_dir("apps", tar_path)), 
            ("nextbox",     lambda: self.export_dir("nextbox", tar_path)),
            ("config",      lambda: self.export_dir("config", tar_path)),
            ("letsencrypt", lambda: self.export_dir("letsencrypt", tar_path)),
        ]

        if not tar_path.exists():
            os.makedirs(tar_path.as_posix())

        self.start_meta(tar_path)
        
        failed = False
        for step_key, step_func in steps:
            self.update_meta(tar_path, {"substate": step_key})
            ret = step_func()

            # blocking call, eval directly and yield state
            if step_key == "sql":
                if ret == True:
                    yield ("finished", ("sql", "export"), 100)
                    continue
                else:
                    self.update_meta(tar_path, {"state": "failed"})
                    failed = True
                    yield ("failed", ("sql", "export"), 100)
                    break

            # non-blocking call(s) check_progress() and yield state
            while True:
                act, desc, percent = self.check_progress()
                if act != "active":
                    if act == "failed":
                        failed = True
                    yield (act, desc, 100)
                    break
                sleep(1)
                yield (act, desc, percent)
        
        # finalize meta (only on success)
        if not failed:
            self.end_meta(tar_path)
            

    ###
    ### convinience, yield-based full-import (use with StopIteration)
    ###
    def full_import(self, src_path):
        steps = [
            ("sql",         lambda: self.import_sql(src_path)),
            ("data",        lambda: self.import_dir("data", src_path)), 
            ("apps",        lambda: self.import_dir("apps", src_path)), 
            ("nextbox",     lambda: self.import_dir("nextbox", src_path)),
            ("config",      lambda: self.import_dir("config", src_path)),
            ("letsencrypt", lambda: self.import_dir("letsencrypt", src_path)),
        ]

        if not src_path.exists():
            os.makedirs(src_path.as_posix())

        self.check_backup(src_path)

        failed = False
        for step_key, step_func in steps:
            # blocking step (sql)
            ret = step_func()

            # blocking call, eval directly and yield state
            if step_key == "sql":
                if ret == True:
                    yield ("finished", ("sql", "import"), 100)
                    continue
                else:
                    failed = True
                    yield ("failed", ("sql", "import"), 100)
                    break

            # non-blocking call(s) check_progress() and yield state
            while True:
                act, desc, percent = self.check_progress()
                if act != "active":
                    if act == "failed":
                        failed = True
                    yield (act, desc, 100)
                    break
                sleep(1)
                yield (act, desc, percent)


if __name__ == "__main__":
    from time import sleep 

    back = RawBackupRestore()
    
    tar_path = Path("/srv/test")
    it = back.full_export(tar_path)
    while True:
        try:
            state, (who, what), percent = next(it)
            print(state, who, what, percent)
        except StopIteration:
            print ("done")
            break

    it = back.full_import(tar_path)
    while True:
        try:
            state, (who, what), percent = next(it)
            print(state, who, what, percent)
        except StopIteration:
            print ("done")
            break

    tar_path = Path("/srv/test2")
    it = back.full_export(tar_path)
    while True:
        try:
            state, (who, what), percent = next(it)
            print(state, who, what, percent)
        except StopIteration:
            print ("done")
            break


    #print(back.export_sql())
    # import time
    # back.rsync_dir("/home/dariball/heap/nzb/dst", "/home/dariball/heap/nzb/dst2")
    # while back.rsync_proc.running:
    #     #print(back.rsync_proc.output)
    #     print(back.rsync_proc.parsed)
    #     time.sleep(0.3)
    # print(back.rsync_proc.parsed)
        
    #print(back.rsync_proc.returncode)
    #print(back.rsync_proc.output)
    #print(back.rsync_proc.cmd)
    #print(back.rsync_proc.get_new_output())
    #print(back.rsync_proc.output)

    #
    #	# First, drop the database (if any)
	#run_command "Dropping existing database" run-mysql -e "DROP DATABASE nextcloud"
	#run_command "Creating new database" run-mysql -e "CREATE DATABASE nextcloud"
	#run_command "Granting database privileges to existing user" \
	#            run-mysql -e "GRANT ALL PRIVILEGES ON nextcloud.* TO 'nextcloud'@'localhost'"


	# Now restore the database 
    ##	echo "Importing database..."
    ##	if ! run-mysql nextcloud < "$database_backup"; then
    ##		echo "Unable to import database"
	##	exit 1
	##fi

    #
    #
    #