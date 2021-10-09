import os
import sys
import pytest
from pathlib import Path

sys.path.append("..")

os.environ["PYTEST_RUNNING"] = "1"

from nextbox_daemon.docker_control import DockerControl


@pytest.fixture
def obj():
    
    return "out"

@pytest.fixture
def tmpl():
    with open("templates/test.conf") as fd:
        return fd.read()



def test_found_template_files(obj):
    pass


