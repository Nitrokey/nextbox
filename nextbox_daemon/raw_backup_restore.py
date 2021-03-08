
from pathlib import Path
from filelock import FileLock
import shutil

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.nextcloud import Nextcloud


class RawBackupRestore:
    data_dir = "/srv/nextcloud/data"
    apps_dir = "/srv/nextcloud/custom_apps"
    db_env = "/usr/lib/nextbox-compose/db.env"
    
    db_export_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysqldump nextcloud -u root --lock-tables --password={pwd} > {path}"
    db_import_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysql nextcloud -u root --password={pwd} < {path}"
    db_cmd = "/usr/bin/docker exec nextbox-compose_db_1 /usr/bin/mysql -u root --password={pwd} -e '{sql}'"
    
    rsync_base_cmd = "/usr/bin/rsync -av {src} {tar}"
    rsync_stats_cmd = "/usr/bin/rsync -a --dry-run --stats {src} {tar}"

    def __init__(self):
        self.nc = Nextcloud()

        self.rsync_proc = None
        self.activity_desc = None
            
    def rsync_dir(self, src_dir, tar_dir):
        cmd = self.rsync_stats_cmd.format(src=src_dir, tar=tar_dir)
        cr = CommandRunner(cmd, block=True)
        num_files = None
        for line in cr.output:
            if "Number of regular files transferred:" in line:
                try:
                    num_files = int(line.split(":")[1].strip())
                except ValueError:
                    num_files = None
                    log.warning("failed parsing number of expected files")
                break
        
        if num_files is None:
            log.warning(f"cannot determine number of files for rsync from: {src_dir} to: {tar_dir}")
            num_files = 1

        if num_files == 0:
            log.info("dry-run reports 0 files to transfer")

        def parse(line, data_dct):
            data_dct.setdefault("line", 0)
            data_dct.setdefault("ratio", 0)
            data_dct["num_files"] = num_files
            data_dct["line"] += 1
            data_dct["ratio"] = round(min(1, max(0, data_dct["line"] / num_files)), 2) * 100

        cmd = self.rsync_base_cmd.format(src=src_dir, tar=tar_dir)
        self.rsync_proc = CommandRunner(cmd, cb_parse=parse)
        return False

    def check_progress(self):
        if self.activity_desc:
            if self.rsync_proc:
                if self.rsync_proc.parsed:
                    return "active", self.activity_desc, self.rsync_proc.parsed.get("ratio", 0)
                if self.rsync_proc.returncode == 0:
                    self.rsync_proc = None
                    out = "finished", self.activity_desc, 100.0
                    self.activity_desc = None
                    return out
        return "inactive", self.activity_desc, 0
        
        
    def export_data(self, tar_dir):
        log.info("starting data export")
        self.activity_desc = "data export"
        ret = self.rsync_dir(self.data_dir, tar_dir)
        if ret:
            log.info("finished data export")


    def import_data(self, src_dir):
        log.info("starting data import")
        self.activity_desc = "data import"
        ret = self.rsync_dir(src_dir, self.data_dir)
        if ret:
            log.info("finished data import")

    def export_apps(self, tar_dir):
        log.info("starting apps export")
        self.activity_desc = "apps export"
        ret = self.rsync_dir(self.data_dir, tar_dir)
        if ret:
            log.info("finished apps export")

    def import_apps(self, src_dir):
        log.info("starting apps import")
        self.activity_desc = "apps import"
        ret = self.rsync_dir(src_dir, self.data_dir)
        if ret:
            log.info("finished apps import")

    def get_sql_password(self):
        with Path(self.db_env).open() as fd:
            for line in fd:
                if "MYSQL_ROOT_PASSWORD" in line:
                    key, val = line.split("=", 1)
                    return val.strip()

    def export_sql(self, tar_path):
        pwd = self.get_sql_password()
        if pwd is None:
            log.error("cannot get sql password for export, aborting...")
            return False
        
        self.nc.set_maintenance_on()

        #tmp_tar_path_inside = "/var/lib/mysql/dump.sql"
        #tmp_tar_path_outside = "/srv/mariadb/dump.sql"
        cmd = self.db_export_cmd.format(pwd=pwd, path=tar_path)
        cr = CommandRunner(cmd, block=True, shell=True)
        
        self.nc.set_maintenance_off()

        #shutil.move(tmp_tar_path_outside, tar_path)

        return cr.returncode == 0


    def import_sql(self, src_path):
        #tmp_src_path_inside = "/var/lib/mysql/dump.sql"
        #tmp_src_path_outside = "/srv/mariadb/dump.sql"
        
        pwd = self.get_sql_password()
        if pwd is None:
            log.error("cannot get sql password for export, aborting...")
            return False

        if not Path(src_path).exists():
            log.error("sql-import data path not found, aborting...")
            return False

        #shutil.move(src_path, tmp_src_path_outside)

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
        cmd = self.db_import_cmd.format(pwd=pwd, path=src_path)
        cr = CommandRunner(cmd, block=True, shell=True)
        
        self.nc.set_maintenance_off()

        return cr.returncode == 0



if __name__ == "__main__":
    back = RawBackupRestore()
    #print(back.export_sql())
    import time
    back.rsync_dir("/home/dariball/heap/nzb/dst", "/home/dariball/heap/nzb/dst2")
    while back.rsync_proc.running:
        #print(back.rsync_proc.output)
        print(back.rsync_proc.parsed)
        time.sleep(0.3)
    print(back.rsync_proc.parsed)
        
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