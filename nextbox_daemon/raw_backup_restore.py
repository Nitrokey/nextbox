import yaml
import os
import time
from pathlib import Path
from datetime import datetime
from filelock import FileLock
import shutil
import yaml
import re

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.nextcloud import Nextcloud, NextcloudError
from nextbox_daemon.config import log, cfg
from nextbox_daemon.services import services
from nextbox_daemon.certificates import Certificates


class RawBackupRestore:
    dirs = {
        "data":         "/srv/nextcloud/data",
        "apps":         "/srv/nextcloud/custom_apps",
        "nextbox":      "/srv/nextbox",
        "config":       "/srv/nextcloud/config",
        "letsencrypt":  "/srv/letsencrypt",
    }

    nextbox_db_env = "docker.env"
    nextbox_conf = "nextbox.conf"
    nextbox_rtun = "rtun.yaml"

    sql_dump_fn = "dump.sql"

    db_export_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysqldump nextcloud -u root --lock-tables --password={pwd} > {path}"
    db_import_cmd = "/usr/bin/docker exec -i nextbox-compose_db_1 /usr/bin/mysql {db} -u root --password={pwd} < {path}"
    db_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysql -u root --password={pwd} -B --disable-column-names -e '{sql}'"

    ### for mysql export use: "--result-file=file.sql"

    ### for mysql import use "SOURCE /path/to/filename.sql"


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

    def rsync_dir(self, key, src_dir, tar_dir, block_main=False):
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
        self.rsync_proc = CommandRunner(cmd, cb_parse=parse, block=block_main)
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
        
    def import_dir(self, key, src_dir, block=False):
        self.activity_desc = (key, "import")
        src_dir = Path(src_dir)
        key_path = Path(self.dirs[key])
        src_path = src_dir / key_path.name
        tar_path = key_path.parent
        self.rsync_dir("data", src_path.as_posix(), tar_path.as_posix(), block_main=block)
        log.info(f"starting {key} import")
        
    def get_env_data(self, docker_env_path=None):
        if docker_env_path is None:
            docker_env_path = Path(self.dirs["nextbox"]) / self.nextbox_db_env

        dct = {}
        with Path(docker_env_path).open() as fd:
            for line in fd:
                toks = line.split("=")
                if len(toks) == 2:
                    key, val = toks
                    dct[key.strip()] = val.strip()
        return dct

    def set_env_data(self, docker_env_path, data_dct):
        with Path(docker_env_path).open("w") as fd:
            for key, val in sorted(data_dct.items()):
                fd.write(f"{key}={val}\n")
        log.debug(f"(re)wrote {docker_env_path} during restore")

    def export_sql(self, tar_path):
        db_env_dct = self.get_env_data()
        pwd = db_env_dct["MYSQL_ROOT_PASSWORD"]
        if pwd is None:
            log.error("cannot get sql password for export, aborting...")
            return False
        
        try:
            self.nc.set_maintenance_on()
        except NextcloudError as e:
            log.error("could not switch on maintainance mode, stopping restore", exc_info=e)
            return False

        tar_sql_path = Path(tar_path) / self.sql_dump_fn
        cmd = self.db_export_cmd.format(pwd=pwd, path=tar_sql_path.as_posix())
        cr = CommandRunner(cmd, block=True, shell=True)
        
        try:
            self.nc.set_maintenance_off()
        except NextcloudError as e:
            log.error("could not switch off maintainance mode, stopping restore", exc_info=e)
            return False

        upd = {"size_sql": os.path.getsize(tar_sql_path.as_posix())}
        self.update_meta(tar_path, upd)

        return cr.returncode == 0


    def sql_move_all_tables(self, root_pwd, src_db, tar_db):
        # get all tables from source db
        cmd = self.db_cmd.format(pwd=root_pwd, sql=f"USE {src_db}; show tables")
        cr = CommandRunner.retries(5, cmd, block=True)
        
        if cr.returncode != 0:
            log.error(f"failed determining all tables in {src_db}")
            return False

        # build mass-table-rename query and run it to move 'src_db.*' to 'tar_db.*'
        tables = [f"{src_db}.{tbl.strip()} to {tar_db}.{tbl.strip()}" \
            for tbl in cr.output if tbl.strip()]
        query = "rename table " + ", ".join(tables)
        cmd = self.db_cmd.format(pwd=root_pwd, sql=query)
        cr = CommandRunner.retries(5, cmd, block=True)
        
        return cr.returncode == 0

    def import_sql(self, src_path):
        db_env_dct = self.get_env_data()
        pwd = db_env_dct["MYSQL_ROOT_PASSWORD"]
        
        if pwd is None:
            log.error("cannot get (root) sql password for import, aborting...")
            return False

        src_sql_path = Path(src_path) / self.sql_dump_fn
        if not src_sql_path.exists():
            log.error("sql-import data path not found, aborting...")
            return False

        # drop (new) database
        cmd = self.db_cmd.format(pwd=pwd, sql="DROP DATABASE IF EXISTS new_nextcloud")
        cr = CommandRunner.retries(5, cmd, block=True)
        
        # create new database
        cmd = self.db_cmd.format(pwd=pwd, sql="CREATE DATABASE new_nextcloud")
        cr = CommandRunner.retries(5, cmd, block=True)
        
        # import sql-dump
        cmd = self.db_import_cmd.format(db="new_nextcloud", pwd=pwd, path=src_sql_path.as_posix())
        cr = CommandRunner(cmd, block=True, shell=True)
        
        # exit here if import failed, no changes done to live-db (nextcloud)
        if cr.returncode != 0:
            cr.log_output()
            log.error("failed importing sql-dump into new database")
            return False

        log.info("success importing sql-dump into temp database")
        try:
            self.nc.set_maintenance_on()
        except NextcloudError as e:
            log.error("could not switch on maintainance mode, stopping restore")
            log.error(exc_info=e)
            return False

        # drop databases (old_nextcloud)
        cmd = self.db_cmd.format(pwd=pwd, sql="DROP DATABASE IF EXISTS old_nextcloud")
        cr = CommandRunner.retries(5, cmd, block=True)
        
        # create new database (old_nextcloud) to move 'nextcloud' into
        cmd = self.db_cmd.format(pwd=pwd, sql="CREATE DATABASE old_nextcloud")
        cr = CommandRunner.retries(5, cmd, block=True)
        
        # move current to old_nextcloud, make thus nextcloud will be empty
        res = self.sql_move_all_tables(pwd, "nextcloud", "old_nextcloud")
        if not res:
            log.error("failed moving tables from 'nextcloud' to 'old_nextcloud'")

        # move newly imported database into live database nextcloud
        self.sql_move_all_tables(pwd, "new_nextcloud", "nextcloud")
        if not res:
            log.error("failed moving tables from 'new_nextcloud' to 'nextcloud'")

        try:
            self.nc.set_maintenance_off()
        except NextcloudError as e:
            log.error("could not switch off maintainance mode, stopping restore", exc_info=e)
            return False

        log.info("completed sql-database import")
        return True

    def import_nextbox_dir(self, src_path):
        # copy rtun.yaml
        p = src_path / "nextbox" / self.nextbox_rtun
        if p.exists():
            shutil.copy(src_path / "nextbox" / self.nextbox_rtun, self.dirs["nextbox"])

        # copy nextbox.conf
        shutil.copy(src_path / "nextbox" / self.nextbox_conf, self.dirs["nextbox"])
        
        # skipping docker.env, as we always keep the one on the device!

        return True

    def import_config_dir(self, src_path):
        # regulary copy over all files
        self.import_dir("config", src_path, block=True)

        log.info("copied configs done - updating db-password")

        # afterwards make sure the password for sql is correct inside config.php
        cfg_path = Path(self.dirs["config"]) / "config.php"
        cfg_content = cfg_path.read_text()

        # get pass from docker.env
        db_env_dct = self.get_env_data()
        dbpass = db_env_dct["MYSQL_PASSWORD"]

        # read config, regex dbpassword, replace with new pass (from docker.env)
        pat = re.compile(r"'dbpassword'[^=]*=>[^']*'([^']*)'[^,]*,")
        res = pat.search(cfg_content)
        old_pass = res.group()
        new_pass = f"'dbpassword' => '{dbpass}',"
        with cfg_path.open("w") as fd:
            fd.write(cfg_content.replace(old_pass, new_pass))

        log.info("updated config.php with 'nextcloud' db password")

        return True

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
            "state":    "completed", 
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

    ###
    ### check some path for containing a valid backup
    ### 
    def check_backup(self, src_path):
        """Check `path` for a valid backup"""
        
        src_path = Path(src_path)
        
        # check for flag file
        if not (src_path / "NEXTBOX_BACKUP.OK").exists():
            log.error(f"check cancel - {src_path}: 'NEXTBOX_BACKUP.OK' missing")
            return False
        
        # read meta info file
        try:
            info = self.read_meta(src_path)
        except FileNotFoundError:
            log.error(f"check cancel - {src_path}: meta-info not found")
            return False
        
        # check for correct state
        if info["state"] != "completed":
            log.error(f"check cancel - {src_path}: meta-info state not 'completed'")
            return False

        # check for all sizes > 0 and src_dirs (+sql-dump) exist in backup
        for key, val in info.items():
            if key.startswith("size_"):
                _, what = key.split("_")
                # check meta-size > 0
                if not val > 0 and what not in ["letsencrypt", "apps"]:
                    log.error(f"check cancel - {src_path}: size for '{what}'' not > 0")
                    return False
                # check existance of dir
                if what != "sql":
                    p = src_path / Path(self.dirs[what]).name
                    if not p.exists():
                        log.error(f"check cancel - {src_path}: {p} not found for restoring: {what}")
                        return False
                # or sql dump file
                else:
                    p = src_path / self.sql_dump_fn
                    if not p.exists():
                        log.error(f"check cancel - {src_path}: {p} not found for db-restore")
                        return False
        return True

    def find_backups(self, paths):
        """search inside `paths` for valid backup directories"""
        out = {}
        for path in paths:
            out[path] = []
            for item in Path(path).iterdir():
                if item.is_dir() and self.check_backup(item):
                    out[path].append({
                        "owner": path,
                        "path": item.as_posix(),
                        "name": item.name,
                        "info": self.read_meta(item.as_posix())
                    })
        return out
    
    ###
    ### convinience, yield-based full-export (use with StopIteration)
    ###
    def full_export(self, tar_path):
        if not isinstance(tar_path, Path):
            tar_path = Path(tar_path)
        
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
                time.sleep(1)
                yield (act, desc, percent)
        
        # finalize meta (only on success)
        if not failed:
            self.end_meta(tar_path)
            cfg["config"]["last_backup"] = datetime.now().timestamp()
            cfg.save()
            yield ("completed", ("all", "export"), 100)

            

    ###
    ### convinience, yield-based full-import (use with StopIteration)
    ###
    def full_import(self, src_path):
        if not isinstance(src_path, Path):
            src_path = Path(src_path)

        steps = [
            ("sql",         lambda: self.import_sql(src_path)),
            ("config",      lambda: self.import_config_dir(src_path)),
            ("nextbox",     lambda: self.import_nextbox_dir(src_path)),
            ("data",        lambda: self.import_dir("data", src_path)), 
            ("apps",        lambda: self.import_dir("apps", src_path)), 
            ("letsencrypt", lambda: self.import_dir("letsencrypt", src_path)),
        ]

        if not src_path.exists():
            os.makedirs(src_path.as_posix())

        self.check_backup(src_path)

        failed = False
        log.info("starting full import")
        for step_key, step_func in steps:
            log.debug(f"full import step: {step_key}")

            # blocking step (sql)
            ret = step_func()

            # blocking call, eval directly and yield state
            if step_key in ["sql", "nextbox", "config"]:
                if ret == True:
                    log.debug(f"finished import step: {step_key}")
                    yield ("finished", (step_key, "import"), 100)
                    continue
                else:
                    log.debug(f"failed import step: {step_key}")
                    failed = True
                    
                    yield ("failed", (step_key, "import"), 100)
                    break

            # non-blocking call(s) check_progress() and yield state
            while True:
                act, desc, percent = self.check_progress()
                if act != "active":
                    if act == "failed":
                        log.debug(f"failed import step: {step_key}")
                        failed = True
                    else:
                        log.debug(f"finished import step: {step_key}")
                    yield (act, desc, 100)
                    break
                time.sleep(1)
                yield (act, desc, percent)

        # final restore steps
        if not failed:
            # recreate apache config based on current (imported) config
            conf_path = Path(self.dirs["nextbox"]) / self.nextbox_conf
            new_cfg = yaml.safe_load(conf_path.open()).get("config", {})
            has_https = new_cfg.get("https_port")
            if has_https:
                domain = new_cfg.get("domain")
                
                certs = Certificates()
                my_cert = certs.get_cert(domain)
                if not my_cert:
                    log.error(f"expected https/ssl, but could not find certificate: {domain}")
                    log.error("switching apache2 config to non-ssl")
                    certs.set_apache_config(ssl=False)
                    #### naaah this is evil:
                    new_cfg["https_port"] = None
                    dct = {"config": new_cfg}
                    yaml.safe_dump(dct, conf_path.open("w"))
                else:
                    log.info(f"found certificate for {domain} - activating ssl")

                    certs.write_apache_ssl_conf(
                        my_cert["domains"][0], 
                        my_cert["fullchain_path"], 
                        my_cert["privkey_path"]
                    )
                    if not certs.set_apache_config(ssl=True):
                        log.error("failed enabling ssl config for apache")
                    else:
                        log.info("re-enabled ssl for imported configuration")

            log.debug("wrote apache config according to restored data")

            # restart daemon 
            log.info("finalized import - all seems good!")
            log.info(".... restarting daemon")
            services.restart("nextbox-daemon")

            yield ("completed", ("all", "import"), 100)


if __name__ == "__main__":
    from time import sleep 

    back = RawBackupRestore()
    print(back.get_env_data())
    print(back.get_env_data("/srv/nextbox/docker.env"))
    print(back.get_env_data("/media/extra-1/izguzgzu/nextbox/docker.env"))

    # tar_path = Path("/srv/test")
    # it = back.full_export(tar_path)
    # while True:
    #     try:
    #         state, (who, what), percent = next(it)
    #         print(state, who, what, percent)
    #     except StopIteration:
    #         print ("done")
    #         break

    # it = back.full_import(tar_path)
    # while True:
    #     try:
    #         state, (who, what), percent = next(it)
    #         print(state, who, what, percent)
    #     except StopIteration:
    #         print ("done")
    #         break