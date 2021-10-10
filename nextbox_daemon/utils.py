import os
from pathlib import Path
import socket
import shutil
from functools import wraps
import fcntl
import struct

from flask import jsonify, request

from nextbox_daemon.consts import API_VERSION
from nextbox_daemon.config import log, cfg


def error(msg, data=None):
    msg = [msg]
    return jsonify({
        "result": "error",
        "msg": msg,
        "data": data,
        "api": API_VERSION
    })


def success(msg=None, data=None):
    msg = [msg] if msg else []
    return jsonify({
        "result": "success",
        "msg": msg,
        "data": data,
        "api": API_VERSION
    })


def local_ip(network_device="eth0"):
    dev = network_device if isinstance(network_device, bytes) \
        else network_device.encode("utf-8")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    binary_data = fcntl.ioctl(
        sock.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack(b'256s', network_device[:15])
    )
    return socket.inet_ntoa(binary_data)[20:24]


def tail(filepath, num_lines=20):
    p = Path(filepath)
    try:
        lines = p.read_text("utf-8").split("\n")
        if num_lines is None or num_lines < 0:
            return lines
        return lines[-num_lines:]
    except OSError as e:
        log.error(f"read from file {filepath} failed, exception: {e}")
        return None

# decorator for authenticated access
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        
        #if request.remote_addr != "127.0.0.1":
        
        # translates to 172.18.238.0/24
        if not request.remote_addr.startswith("172.18.238."):
            # abort(403)
            return error("not allowed")
        
        return f(*args, **kwargs)
    return decorated
