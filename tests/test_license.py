"""license 生成/验证测试。"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import netcfg_vault.license as lic


def test_generate_and_load(tmp_path, monkeypatch):
    key = lic.generate_license("tester", 50, days=30)
    monkeypatch.setenv("NETCFG_LICENSE", key)
    info = lic.load_license()
    assert info["customer"] == "tester"
    assert info["device_limit"] == 50
    assert lic.effective_device_limit() == 50


def test_expired(tmp_path, monkeypatch):
    key = lic.generate_license("tester", 50, days=-1)
    monkeypatch.setenv("NETCFG_LICENSE", key)
    assert lic.load_license() is None
    assert lic.effective_device_limit() == 5


def test_garbage_key(monkeypatch):
    monkeypatch.setenv("NETCFG_LICENSE", "NCV-GARBAGE!!!!")
    assert lic.load_license() is None
    assert lic.effective_device_limit() == 5


def test_no_license(monkeypatch):
    monkeypatch.delenv("NETCFG_LICENSE", raising=False)
    assert lic.effective_device_limit() == 5
