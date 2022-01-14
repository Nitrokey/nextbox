
import urllib.request, urllib.error
import json
from pathlib import Path
import socket 
import ssl

from nextbox_daemon.config import log
from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.consts import GET_EXT_IP4_URL, GET_EXT_IP6_URL, SYSTEMD_RESOLVE_BIN

class DNSManager:
    def __init__(self):
        pass

    def clear_dns_caches(self):
        CommandRunner([SYSTEMD_RESOLVE_BIN, "--flush-cache"], block=True)
        CommandRunner([SYSTEMD_RESOLVE_BIN, "--reset-server-features"], block=True)

    def get_ipv6(self):
        try:
            return urllib.request.urlopen(GET_EXT_IP6_URL).read().decode("utf-8")
        except urllib.error.URLError:
            ...

    def get_ipv4(self):
        try:
            return urllib.request.urlopen(GET_EXT_IP4_URL).read().decode("utf-8")
        except urllib.error.URLError:
            ...
    
    def resolve_ipv4(self, domain):
        try:
            return socket.gethostbyname(domain)
        except socket.gaierror:
            ...

    def resolve_ipv6(self, domain):
        try:
            return socket.getaddrinfo(domain, None, socket.AF_INET6)[0][-1][0]
        except (socket.gaierror, IndexError):
            ...


if __name__ == "__main__":
    pass