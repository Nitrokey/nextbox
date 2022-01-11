
import os
import yaml
import socket
import sys
import re

hostname = socket.gethostname()
user = os.environ["USER"]

# read registry
with open("registry.yaml") as fd:
    registry = yaml.safe_load(fd)

# check legal user
if registry["user"] != user:
    print("local user does not match the one in the registry!")
    sys.exit(1)

# check legal host
if registry["host"] != hostname:
    print("hostname does not match the one in the registry!")
    sys.exit(1)

# open token file and import all tokens
with open(registry["token_file"]) as fd:
    TOKENS = [tok.strip() for tok in fd.readlines()]

# check for passed serial
if len(sys.argv) != 2:
    print("no serial number provided")
    print("Usage: python3 token_manager.py <serial>")
    sys.exit(1)

# check for valid serial
serial = sys.argv[1]
if not re.match("^[0-9]{8}$", serial):
    print("provided invalid serial number")
    sys.exit(1)

# get token
token_idx = len(registry["serials"]) + registry["offset"]
token = TOKENS[token_idx]

# create registry entry
new_entry = {
    "serial": serial,
    "token": token,
}

# create nextbox.conf
with open("nextbox.conf.tmpl") as fd:
    nextbox_conf = fd.read() \
        .replace("%%TOKEN%%", token) \
        .replace("%%SERIAL%%", serial)

# write nextbox.conf
with open("nextbox.conf", "w") as fd:
    fd.write(nextbox_conf)

# update and save registry
registry["serials"].append(new_entry)
with open("registry.yaml", "w") as fd:
    yaml.dump(registry, fd)

print("SUCCESS, created nextbox.conf and updated registry")

sys.exit(0)







