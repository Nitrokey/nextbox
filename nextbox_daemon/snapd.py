import socket

import sys
sys.path.append("/snap/nextbox/current/lib/python3.6/site-packages")

import requests
from requests.adapters import HTTPAdapter
from urllib3.connectionpool import HTTPConnectionPool
from urllib3.connection import HTTPConnection

from nextbox_daemon.config import log

# inspired by: https://stackoverflow.com/questions/26964595/whats-the-correct-way-to-use-a-unix-domain-socket-in-requests-framework


class SnapdConnection(HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/run/snapd.socket")


class SnapdConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super().__init__("localhost")

    def _new_conn(self):
        return SnapdConnection()


class SnapdAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return SnapdConnectionPool()


class SnapsManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.mount("http://snapd/", SnapdAdapter())

        self.own_running = set()

    def get_stable_revision(self, name):
        resp = self.session.get(f"http://snapd/v2/find?name={name}")
        revision = resp.json() \
            .get("result")[0].get("channels").get("latest/stable").get("revision")
        return int(revision)

    def get_local_revision(self, name):
        resp = self.session.get(f"http://snapd/v2/snaps/{name}")
        return int(resp.json().get("result").get("revision"))

    def refresh(self, name):
        data = {
            "action": "refresh",
            "snaps":  [name]
        }
        resp = self.session.post(f"http://snapd/v2/snaps", json=data)
        log.debug(f"refresh: {name}")
        self.own_running.add(resp.json().get("change"))
        return resp.json().get("status") == "OK"

    def is_change_done(self, c_id):
        resp2 = self.session.get(f"http://snapd/v2/changes/{c_id}")

        # does not exists, so it's done
        if resp2.json().get("result", {}).get("status", {}):
            return False

        # exists and finished
        if resp2.json().get("result").get("status") == "Done":
            log.debug("change job done")
            return True

        # still running
        log.debug(f"still running change job: {c_id}")
        return False

    def any_change_running(self):
        for c_id in tuple(self.own_running):
            if not self.is_change_done(c_id):
                return True
            self.own_running.remove(c_id)
        return False

    @property
    def running(self):
        resp = self.session.get("http://snapd/v2/changes")
        print(resp.json())
        c_ids = resp.json().get("result")
        return c_ids

    def check_and_refresh(self, snaps):
        updated = []
        for snap in snaps:
            if self.get_stable_revision(snap) != self.get_local_revision(snap):
                log.info(f"refreshing: {snap}")
                self.refresh(snap)
                updated.append(snap)
            else:
                log.debug(f"no need to refresh: {snap}")
        return updated