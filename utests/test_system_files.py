import sys
import pytest
from pathlib import Path

sys.path.append("..")

from nextbox_daemon.system_files import SystemFiles


@pytest.fixture
def obj():
    p_file_plain = "/tmp/nextbox-test/test.conf"
    SystemFiles.system_files_map["test.conf"] = p_file_plain
    out = SystemFiles("templates")
    
    p_file = Path(p_file_plain)
    p_dir = Path("/tmp/nextbox-test")
    
    if p_file.exists():
        p_file.unlink()
    if p_dir.exists():
        p_dir.rmdir()
        
    p_dir.mkdir()
    return out

@pytest.fixture
def tmpl():
    with open("templates/test.conf") as fd:
        return fd.read()

@pytest.fixture
def data():
    return {
        "place1": "abc",
        "other":  "extra\"$§%'",
        "bla": "123",
        "wh000t": "whatever"
    }

@pytest.fixture
def final():
    return """sup abc
uha now we code ${bla},extra"$§%'${pytemplate}and
some json:
{
    "foo": 123,
    "blub": whatever
}
"""


def test_found_template_files(obj):
    assert len(obj.template_files) == 1

def test_placeholders(obj, tmpl):
    ret = obj.get_placeholders(tmpl)
    expected = ["place1", "other", "bla", "wh000t"]
    assert all(item in expected for item in ret)
    assert len(expected) == len(ret)

def test_replace(obj, tmpl, data, final):
    ret = obj.replace_placeholders(tmpl, **data)
    print (len(ret), len(final))
    assert ret == final

def test_ensure(obj, final, data):
    res = obj.ensure_file("test.conf", **data)
    assert res

def test_ensure2(obj, final, data):
    res = obj.ensure_file("test.conf", **data)
    assert res

    res = obj.ensure_file("test.conf", **data)
    assert not res
    
def test_ensure3(obj, final, data):
    res = obj.ensure_file("test.conf", **data)
    assert res

    with open(obj.system_files_map["test.conf"], "w") as fd:
        fd.write("9032u4oijf\n9udu9few0f")

    res = obj.ensure_file("test.conf", **data)
    assert res
    
    res = obj.ensure_file("test.conf", **data)
    assert not res



