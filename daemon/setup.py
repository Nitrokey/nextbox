import os
from setuptools import setup

setup(
    name = "nextbox-daemon",
    version = "0.0.3",
    author = "Markus Meissner - Nitrokey",
    author_email = "nextbox@nitrokey.com",
    description = "The Nitrokey - NextBox System Control Daemon",
    license = "GPL",
    packages = ["nextbox_daemon", "nextbox_daemon.api"],
    entry_points = {
        'console_scripts' : ['nextbox-daemon = nextbox_daemon.start:main']
    },
    data_files = [
        #('share/nextbox-daemon/compose/', ['nextcloud/docker-compose.yml']),
        #('share/nextbox-daemon/compose/', ['nextcloud/db.env']),
        #('lib/systemd/system/', ['nextbox-daemon.service']),
    ],
    classifiers=[
        "Development Status :: 3 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GPL License",
    ],
)
