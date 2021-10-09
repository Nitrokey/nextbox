import socket
from pathlib import Path
from datetime import datetime as dt
from io import BytesIO
import time
import tarfile

import docker

from nextbox_daemon.config import log, cfg


class DockerControlException(Exception): pass
class ContainerNotFound(DockerControlException): pass
class ContainerNotRunning(DockerControlException): pass
class ErrorDuringCommandExecution(DockerControlException): pass


# helper functions to pack and unpack archive for docker copy_to & _from
def archive_from_path(path):
    tar_fd = BytesIO()
    tar = tarfile.TarFile(fileobj=tar_fd, mode="w")
    contents = open(path, "rb").read()

    info = tarfile.TarInfo(name=Path(path).name)
    info.size = len(contents)
    info.mtime = time.time()
    info.mode = 666 

    tar.addfile(info, BytesIO(contents))
    tar.close()

    tar_fd.seek(0)
    return tar_fd, info

def file_from_archive(archive_fd):
    tar = tarfile.TarFile(fileobj=archive_fd, mode="r")
    # we always transport just one file for now!
    info = tar.getmembers()[0]
    file_fd = tar.extractfile(info)
    return file_fd, info
    


class DockerControl:

    names = {
        "nextcloud": "nextbox-compose_app_1", 
        "cron":      "nextbox-compose_cron_1", 
        "redis":     "nextbox-compose_redis_1", 
        "db":        "nextbox-compose_db_1"
    }

    @property
    def api(self):
        return docker.from_env()

    def get(self, which):
        if which not in self.names:
            raise ContainerNotFound(which)

        c_name = self.names[which]

        if c_name not in [x.name for x in self.api.containers.list()]:
            raise ContainerNotRunning(which)

        return self.api.containers.get(c_name)

    def is_running(self, c_name):
        return self.get(c_name).status == "running"

    def seconds_running(self, c_name):
        if not self.is_running(c_name):
            raise ContainerNotRunning(c_name) 

        started = self.get(c_name).attrs \
            .get("State", {}).get("StartedAt")

        started = dt.fromisoformat(started.split(".")[0])

        secs = (dt.now() - started).total_seconds()
        if secs == 0:
            secs += 1
        return secs

    def copy_to(self, c_name, path):
        archive_fd, info = archive_from_path(path)
        return self.get(c_name).put_archive(path="/tmp", data=archive_fd), info

    def copy_from(self, c_name, path, write_to=None):
        archive_fd, _ = self.get(c_name).get_archive(path)
        file_fd, info = file_from_archive(BytesIO(b"".join(archive_fd)))
        out = BytesIO(file_fd.read())
        if write_to:
            file_fd.seek(0)
            with open(write_to, "wb") as fd:
                fd.write(file_fd.read())
        return out, info
        
    def exec(self, c_name, cmd):
        return self.get(c_name).exec_run(cmd)
        