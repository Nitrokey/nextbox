import os
import sys
import re
from pathlib import Path
import signal
import time

import shutil
import socket
import ssl
import json


from queue import Queue

from flask import Flask, render_template, request, flash, redirect, Response, \
    url_for, send_file, Blueprint, render_template, jsonify, make_response

from nextbox_daemon.utils import error, success, \
    tail, local_ip, cleanup_certs, requires_auth

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.consts import *
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_mgr, job_queue, worker
from nextbox_daemon.jobs import TrustedDomainsJob, ProxySSHJob

from nextbox_daemon.api.storage import storage_api
from nextbox_daemon.api.backup import backup_api
from nextbox_daemon.api.generic import generic_api
from nextbox_daemon.api.remote import remote_api



app = Flask(__name__)
app.secret_key = "123456-nextbox-123456" #cfg["secret_key"]

app.register_blueprint(generic_api)
app.register_blueprint(backup_api)
app.register_blueprint(remote_api)
app.register_blueprint(storage_api)


#@app.before_request
#def limit_remote_addr():
#    if request.remote_addr != '10.20.30.40':
#        abort(403)  # Forbidden
#

### CORS section
@app.after_request
def after_request_func(response):
    origin = request.headers.get('Origin')

    response.headers.add('Access-Control-Allow-Credentials', 'true')
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'x-csrf-token')
        response.headers.add('Access-Control-Allow-Headers', 'requesttoken')
        response.headers.add('Access-Control-Allow-Methods',
                            'GET, POST, OPTIONS, PUT, PATCH, DELETE')
    if origin:
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', request.remote_addr)


    #response.headers.add('Access-Control-Allow-Origin', cfg["config"]["domain"])

    #if not origin:
    #    response.headers.add('Access-Control-Allow-Origin', "192.168.10.129")
    #    response.headers.add('Access-Control-Allow-Origin', "192.168.10.47")

    return response
### end CORS section



def signal_handler(sig, frame):
    global job_queue, worker

    print("Exit handler, delivering worker exit job now")
    job_queue.put("exit")
    worker.join()
    print("Joined worker - exiting now...")
    
    sys.exit(1)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    job_mgr.register_job(TrustedDomainsJob)
    job_mgr.register_job(ProxySSHJob)

    worker.start()

    app.run(host="0.0.0.0", port=18585, debug=True, threaded=True, processes=1, use_reloader=False)

    signal.pause()


if __name__ == "__main__":
    main()

# cat /sys/class/thermal/thermal_zone0/temp
