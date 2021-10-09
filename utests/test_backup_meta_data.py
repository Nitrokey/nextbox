import os
import sys
import pytest
from pathlib import Path
from time import sleep
import yaml
from datetime import datetime as dt

sys.path.append("..")


os.environ["PYTEST_RUNNING"] = "1"

from nextbox_daemon.backup_meta_data import BackupMetaData

backup_dir = "backup_test/tar"
src_dir = "backup_test/src"

stats_data = {
    'aa': {'count': 2, 'size': 42}, 
    'bb': {'count': 2, 'size': 0}, 
    'cc_1': {'count': 1, 'size': 0}, 
    'cc_2': {'count': 5, 'size': 2288}, 
    'cc_3': {'count': 3, 'size': 8}, 
    'sql': {'count': 0, 'size': 0}
}

yaml_sample = {
    'version': 2, 
    'nc_version': (1, 2, 3), 
    'state': 'started', 
    'substate': 'init', 
    'components': {
        'aa': {'count': 2, 'size': 42}, 
        'bb': {'count': 2, 'size': 0}, 
        'cc_1': {'count': 1, 'size': 0}, 
        'cc_2': {'count': 5, 'size': 2288}, 
        'cc_3': {'count': 3, 'size': 8}, 
        'sql': {'count': 0, 'size': 0}
    }, 
    'started': '2021-10-09 14:06:29.169206', 
    'ended': None
}

old_data = {
    "state":        "started",
    "substate":     "init",
    "size_aa":      54342,
    "size_bb":      1234,
    "size_cc_1":    2324,
    "size_cc_2":    4342,
    "started":      str(dt.now()),
    "ended":        str(dt.now()),
}


def setup_module(module):
    c = os.system

    c("rm -rf backup_test")

    c("mkdir -p backup_test/src")
    
    c("mkdir -p backup_test/src/aa")
    c("echo 'abcabcbcabsicbsau\nioasjdiasodjidsa\nioasdj' > backup_test/src/aa/testfile_aa.txt")

    c("mkdir -p backup_test/src/bb")
    c("touch backup_test/src/bb/testfile_bb.txt")

    c("mkdir -p backup_test/src/cc")
    
    c("mkdir -p backup_test/src/cc/1")
    
    c("mkdir -p backup_test/src/cc/2")
    c("echo 123ssfweewfiofewofwej > backup_test/src/cc/2/testfile.txt")
    c("echo 123ssfweewfiofewofwej > backup_test/src/cc/2/testfile2.txt")
    c("echo 123ssfweewfiofewofwej > backup_test/src/cc/2/testfile3.txt")
    c("echo 123ssfweewfiofewofwej > backup_test/src/cc/2/testfile5.txt")
    for _ in range(100):
        c("echo 123ssfweewfiofewofwej >> backup_test/src/cc/2/testfile5.txt")

    c("mkdir -p backup_test/src/cc/3")
    c("echo 123 > backup_test/src/cc/3/testfile.txt")
    c("echo 999 > backup_test/src/cc/3/testfile2.txt")
    
    c("mkdir -p backup_test/tar")

    BackupMetaData.components = {
        "aa":   "aa",
        "bb":   "bb",
        "cc_1": "cc/1",
        "cc_2": "cc/2",
        "cc_3": "cc/3",
        "sql":  "dump.sql"
    }

def teardown_module(module):
    c = os.system
    c("rm -rf backup_test")

@pytest.fixture
def obj():
    return None
    #return BackupMetaData(backup_dir)

def test_meta_path():
    obj = BackupMetaData(backup_dir)
    assert obj.file_path == Path("backup_test/tar/" + BackupMetaData.meta_data_fn)

def test_get_stats():
    obj = BackupMetaData(src_dir)
    my_stats = obj.get_stats()
    assert my_stats == stats_data

def test_get_stats_strict():
    obj = BackupMetaData(src_dir)
    my_stats = obj.get_stats(strict=True)
    assert my_stats == stats_data
    

def test_get_updated():
    obj = BackupMetaData(src_dir)
    obj.nextcloud = type("_", (), {"get_version":lambda: (1,2,3)})

    obj.update()

    for key in ["state", "substate", "components", "version", "nc_version", "ended"]:
        assert obj.data[key] == yaml_sample[key]


@pytest.fixture
def stub():
    p = Path(src_dir) / BackupMetaData.meta_data_fn
    with p.open("w") as fd:
        yaml.dump(old_data, fd)

    obj = BackupMetaData(src_dir)
    obj.nextcloud = type("_", (), {"get_version":lambda: (1,2,3)})
    return p, obj

def test_get_updated_from_1_and_missing(stub):

    p, obj = stub
    obj.load(get_missing=True)

    p.unlink()

    for key in ["state", "substate", "components", "version"]:
        assert obj.data[key] == yaml_sample[key]

    # cannot determine after actual backup
    assert obj.data["nc_version"] == None
    
    assert obj.data["started"] is not None
    assert obj.data["ended"] == old_data["ended"]


def test_get_updated_from_1(stub):
    
    p, obj = stub
    obj.load()

    p.unlink()

    for key in ["state", "substate", "version"]:
        assert obj.data[key] == yaml_sample[key]

    # cannot determine after actual backup
    assert obj.data["nc_version"] == None

    assert obj.data["started"] is not None
    assert obj.data["ended"] == old_data["ended"]

    assert obj.data["components"]["aa"]["size"] == 54342
    assert obj.data["components"]["bb"]["size"] == 1234
    assert obj.data["components"]["cc_1"]["size"] == 2324
    assert obj.data["components"]["cc_2"]["size"] == 4342

    assert all(val["count"] is None for key, val in obj.data["components"].items())

    #assert obj.data == yaml_sample



def test_get_transfer_stats():

    obj = BackupMetaData(src_dir)
    obj.nextcloud = type("_", (), {"get_version":lambda: (1,2,3)})

    stats = obj.get_stats("backup_test/tar")

    expected = {
        'aa': {'count': 2, 'transfer_count': 1, 'size': 42, 'transfer_size': 42}, 
        'bb': {'count': 2, 'transfer_count': 1, 'size': 0, 'transfer_size': 0}, 
        'cc_1': {'count': 1, 'transfer_count': 0, 'size': 0, 'transfer_size': 0}, 
        'cc_2': {'count': 5, 'transfer_count': 4, 'size': 2288, 'transfer_size': 2288}, 
        'cc_3': {'count': 3, 'transfer_count': 2, 'size': 8, 'transfer_size': 8}
    }

    assert expected == stats


def test_round_and_round():

    obj = BackupMetaData(src_dir)
    obj.nextcloud = type("_", (), {"get_version":lambda: (1,2,3)})

    assert not obj.file_path.exists()
    obj.update()
    obj.save()

    org_data = obj.data

    obj2 = BackupMetaData(src_dir)
    assert obj2.file_path.exists()
    obj2.load()
    assert obj2.data == org_data

    obj2.file_path.unlink()
    assert not obj2.file_path.exists()

    obj2.save()

    obj3 = BackupMetaData(src_dir)
    assert obj3.file_path.exists()
    obj3.load()
    assert obj3.data == org_data

    obj3.file_path.unlink()
    assert not obj3.file_path.exists()
