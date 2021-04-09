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

from gunicorn.app.base import BaseApplication

from nextbox_daemon.utils import error, success, \
    tail, local_ip, requires_auth

from nextbox_daemon.command_runner import CommandRunner
from nextbox_daemon.config import cfg, log
from nextbox_daemon.worker import job_mgr, job_queue, worker
from nextbox_daemon.status_board import board
from nextbox_daemon.shield import shield
from nextbox_daemon.jobs import ACTIVE_JOBS

# blueprint for the sub-pages/apis
from nextbox_daemon.api.storage import storage_api
from nextbox_daemon.api.backup import backup_api
from nextbox_daemon.api.generic import generic_api
from nextbox_daemon.api.remote import remote_api


app = Flask(__name__)
app.secret_key = cfg["config"]["nk_token"] if cfg["config"]["nk_token"] else "dummy"

app.register_blueprint(generic_api)
app.register_blueprint(backup_api)
app.register_blueprint(remote_api)
app.register_blueprint(storage_api)

shield.set_led_state("started")

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

    return response
### end CORS section


class NextBoxApplication(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


# register all to-be-activated jobs at job-mgr
for job_cls in ACTIVE_JOBS:
    job_mgr.register_job(job_cls)

# shutdown handler for background-process (dispatched via gunicorn)
def end_background_worker(worker_thread, server):
    global job_queue, worker

    print("exit handler, delivering worker exit job now")
    job_queue.put("exit")
    worker.join()
    print("joined worker - exiting now...")

# start our background-worker-thread
def start_background_worker(worker_thread):
    worker.start()

# main-entrypoint
def main():
    global job_queue, worker

    # rest-api-server (gunicorn) startup-options
    options = {
        "bind": '%s:%s' % ('0.0.0.0', '18585'),
        "workers": 1,
        "threads": 3,
        "log-level": "info",
        "post_worker_init": start_background_worker,
        "worker_exit": end_background_worker
    }

    NextBoxApplication(app, options).run()
    
if __name__ == "__main__":
    main()
    sys.exit(1)
