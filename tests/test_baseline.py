"""Tests for baseline snapshots (set/list/diff/remove)."""
import sys
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from netcfg_vault import baseline


def _mk(dirpath, files):
    shutil.rmtree(dirpath, ignore_errors=True)
    for name, text in files.items():
        p = dirpath / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")


def test_set_list_diff_remove(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    src = tmp_path / "src"
    _mk(src, {"sw1.cfg": "hostname sw1\ninterface Gi1/0/1\n", "sw2.cfg": "hostname sw2\n"})
    assert baseline.cmd_set(str(src), "golden") == 0
    assert (tmp_path / ".netcfg-baselines" / "golden" / "manifest.json").exists()

    # duplicate name rejected
    assert baseline.cmd_set(str(src), "golden") == 2

    # list shows it
    rc = baseline.cmd_list()
    assert rc == 0

    # identical current dir -> no changes
    assert baseline.cmd_diff(str(src), "golden") == 0

    # mutate current -> change detected
    _mk(src, {"sw1.cfg": "hostname sw1\ninterface Gi1/0/2\n", "sw2.cfg": "hostname sw2\n", "sw3.cfg": "hostname sw3\n"})
    assert baseline.cmd_diff(str(src), "golden") == 1

    # remove then diff fails
    assert baseline.cmd_remove("golden") == 0
    assert baseline.cmd_diff(str(src), "golden") == 2


def test_set_missing_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert baseline.cmd_set(str(tmp_path / "nope"), "x") == 2