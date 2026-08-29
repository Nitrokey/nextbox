#!/usr/bin/env python3
import subprocess
import socket
import datetime
import os
import html
import shutil
import signal
import sys
import re
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

OUTPUT_HTML      = "/var/www/html/status.html"
HTTP_PORT        = 8080
REFRESH_INTERVAL = 60

JOURNAL_PATTERNS = [
    ("UAS is ignored for this device, using usb-storage instead", True, "UAS not used warning, pressent"),
    ("Can't start Nextcloud because upgrading", False, "No nextcloud upgrade block"),
]

# Note: Added nextbox-daemon.server here
SERVICES = [
    "sshd.service",
    "networking.service",
    "docker.service",
    "nextbox-daemon.service",
]

# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def run_cmd(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True)
    return p.stdout.strip(), p.stderr.strip(), p.returncode

def get_package_version(pkg_name):
    """
    Returns the installed version of the given Debian package,
    or an error string if the package is not installed.
    """
    # dpkg-query exits non-zero if the package is not installed
    out, err, rc = run_cmd(["dpkg-query", "-W", "-f=${Version}", pkg_name])
    if rc == 0 and out:
        return out
    elif rc == 0:
        return "(no version string returned)"
    else:
        return f"(not installed or error: {err or out})"

def get_host_info():
    """Gather hostname, uptime, and load averages (no disk anymore)."""
    hostname = socket.gethostname()

    up_out, up_err, up_rc = run_cmd(["uptime", "-p"])
    uptime = up_out if up_rc == 0 else f"error: {up_err}"

    la_out, la_err, la_rc = run_cmd(["cat", "/proc/loadavg"])
    if la_rc == 0:
        load1, load5, load15 = la_out.split()[:3]
    else:
        load1 = load5 = load15 = f"error: {la_err}"

    return {
        "hostname": hostname,
        "uptime": uptime,
        "load1": load1,
        "load5": load5,
        "load15": load15,
    }

def check_journal_boot(patterns):
    """
    Scan the entire journal of the current boot for each pattern.
    Patterns should be an iterable of:
       - (string, bool)           => (pattern, should_exist)
       - (string, bool, string)   => (pattern, should_exist, label)
       - bare string (=> must exist, label=pattern)

    Returns a dict mapping each label to (ok:bool, message:str).
    """
    # Normalize into triplets (pattern, should_exist, label)
    normalized = []
    for p in patterns:
        if isinstance(p, tuple):
            if len(p) == 2:
                pattern, should_exist = p
                label = pattern
            elif len(p) == 3:
                pattern, should_exist, label = p
            else:
                raise ValueError("Pattern tuples must be (pat, bool[, label])")
        elif isinstance(p, str):
            pattern, should_exist, label = p, True, p
        else:
            raise ValueError("Each pattern entry must be str or tuple")

        normalized.append((pattern, bool(should_exist), str(label)))

    # Grab whole journal for this boot
    cmd = ["journalctl", "-b", "--no-pager", "--output=short-iso"]
    out, err, rc = run_cmd(cmd)
    if rc != 0:
        # mark all as FAIL
        return {
            label: (False, f"journalctl exit code {rc}, err={err}")
            for _, _, label in normalized
        }

    text = out.lower()
    results = {}
    for pattern, should_exist, label in normalized:
        found = (pattern.lower() in text)
        if should_exist:
            if found:
                results[label] = (True, f"Found required pattern")
            else:
                results[label] = (False, f"Missing required pattern")
        else:
            if found:
                results[label] = (False, f"Forbidden pattern was found")
            else:
                results[label] = (True, f"Forbidden pattern not present")
    return results

def check_services(services):
    status = {}
    for svc in services:
        out, err, rc = run_cmd(["systemctl", "is-active", svc])
        if rc == 0:
            status[svc] = out
        else:
            status[svc] = (out or err or "unknown").strip()
    return status

def render_html(host, nextbox_version, journal_checks, services):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        f"<title>Status of {html.escape(host['hostname'])}</title>",
        "<style>"
        "body{font-family:sans-serif;margin:20px}"
        "table{border-collapse:collapse;width:100%;margin-bottom:2em}"
        "th,td{border:1px solid #ccc;padding:8px}"
        "th{background:#eee}"
        ".error{color:red;font-weight:bold}"
        "pre{background:#f9f9f9;padding:10px}"
        "</style></head><body>",
        f"<h1>Status for {html.escape(host['hostname'])}</h1>",
        f"<p>Generated: {now}</p>",
        # Host Overview (no disk)
        "<h2>Host Overview</h2><table>",
        f"<tr><th>Uptime</th><td>{html.escape(host['uptime'])}</td></tr>",
        f"<tr><th>Load (1m,5m,15m)</th>"
        f"<td>{host['load1']}, {host['load5']}, {host['load15']}</td></tr>",
        f"<tr><th>Nextbox Package</th><td>{html.escape(nextbox_version)}</td></tr>",
        "</table>",
        # Services
        "<h2>Service Status</h2><table><tr><th>Service</th><th>Status</th></tr>"
    ]
    for svc, st in services.items():
        cls = "error" if st.lower() != "active" else ""
        parts.append(
            f"<tr><td>{html.escape(svc)}</td>"
            f"<td class='{cls}'>{html.escape(st)}</td></tr>"
        )
    parts.append("</table>")

    # Journal Matches
    parts.append("<h2>Journal Pattern Checks</h2>")
    parts.append("<table><tr><th>Check</th><th>Status</th><th>Details</th></tr>")
    for label, (ok, message) in journal_checks.items():
        cls    = "" if ok else "error"
        status = "OK" if ok else "ERROR"
        parts.append(
            f"<tr>"
            f"<td>{html.escape(label)}</td>"
            f"<td class='{cls}'>{status}</td>"
            f"<td>{html.escape(message)}</td>"
            f"</tr>"
        )
    parts.append("</table>")

    return "\n".join(parts)

# -------------------------------------------------------------------
# MAIN LOOP + HTTP SERVER
# -------------------------------------------------------------------

def generate_page():
    host    = get_host_info()
    nb_ver  = get_package_version("nextbox")
    journal_checks = check_journal_boot(JOURNAL_PATTERNS)
    svcs    = check_services(SERVICES)
    page    = render_html(host, nb_ver, journal_checks, svcs)

    os.makedirs(os.path.dirname(OUTPUT_HTML), exist_ok=True)
    tmp = OUTPUT_HTML + ".tmp"
    with open(tmp, "w") as f:
        f.write(page)
    os.replace(tmp, OUTPUT_HTML)
    print(f"[{datetime.datetime.now()}] Updated {OUTPUT_HTML}", flush=True)

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/status.html"):
            try:
                with open(OUTPUT_HTML, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_error(404, "Status page not found")
            except Exception as e:
                self.send_error(500, f"Error: {e}")
        else:
            self.send_error(404, "Not Found")

def serve():
    srv = HTTPServer(("0.0.0.0", HTTP_PORT), StatusHandler)
    print(f"Serving on port {HTTP_PORT}", flush=True)
    srv.serve_forever()

def shutdown(signum, frame):
    print("Shutting down...", flush=True)
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, shutdown)
    generate_page()

    # background refresher
    def refresher():
        import time
        while True:
            time.sleep(REFRESH_INTERVAL)
            generate_page()
    threading.Thread(target=refresher, daemon=True).start()

    serve()

