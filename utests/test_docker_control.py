import os
import sys
import pytest
from pathlib import Path
from time import sleep
from io import BytesIO

import docker

sys.path.append("..")

os.environ["PYTEST_RUNNING"] = "1"

from nextbox_daemon.docker_control import DockerControl


name = "test_container"
container = None

example_size_mult = 1024 * 1024
example_file_content = ((b"xz" * 66) + b"\n") * example_size_mult
example_file = "test.example.data"
example_file_from = "test.example2.data"

def stop_container(which):
    con = docker.from_env()
    try:
        old = con.containers.get(which)
        if old:
            try:
                old.kill()
            except Exception as e:
                #print(e)
                pass
            old.stop()
            old.remove()
            sleep(5)
    except Exception as e:
        #print(e)
        pass

def setup_module(module):
    global container
    
    stop_container(name)
    
    con = docker.from_env()
    container = con.containers.run("ubuntu", name=name, detach=True, command="sleep 3600")
    
    while name not in [x.name for x in con.containers.list()]:
        print("waiting for container creation")
        sleep(1)

    while con.containers.get(name).status != "running":
        print (con.containers.get(name).status)
        print ("waiting for container start")
        sleep(1)

    p = Path(example_file)
    chunks = example_file_content.split(b"\n")
    with p.open("wb") as fd:
        for chunk in chunks[:-1]:
            fd.write(chunk + b"\n")
        fd.write(chunks[-1])
        
def teardown_module(module):
    global container
    stop_container(name)

    for path in [example_file, example_file_from]:
        p = Path(path)
        if p.exists():
            p.unlink()
        

@pytest.fixture
def obj():
    DockerControl.names["test"] = name
    dc = DockerControl()
    return dc


def test_is_running(obj):
    assert obj.is_running("test")

def test_seconds_running(obj):
    running_secs = obj.seconds_running("test")
    assert running_secs  > 0
    sleep(1)
    running_secs2 = obj.seconds_running("test")
    assert running_secs2 > running_secs

def test_simple_exec(obj):
    res = obj.exec("test", "echo 1")

    assert res.exit_code == 0
    assert res.output == b"1\n"

def test_simple_exec_error(obj):
    res = obj.exec("test", "xisaoxj")
    assert res.exit_code != 0
    assert b"executable file not found in $PATH" in res.output.strip()

def test_copy_to(obj):
    ret, info = obj.copy_to("test", example_file)
    assert ret

    res = obj.exec("test", "wc -c /tmp/" + example_file)
    wc_len = int(res.output.strip().split(b" ")[0])
    assert wc_len == info.size

def test_copy_from(obj):
    archive_fd, info = obj.copy_from("test", "/tmp/" + example_file)
    assert archive_fd
    assert len(archive_fd.read()) == len(example_file_content) == info.size

def test_copy_from_write(obj):
    ret, info = obj.copy_from("test", "/tmp/" + example_file, example_file_from)
    assert ret

    res = obj.exec("test", "wc -c /tmp/" + example_file)
    wc_len = int(res.output.strip().split(b" ")[0])
    assert wc_len == info.size == len(example_file_content)