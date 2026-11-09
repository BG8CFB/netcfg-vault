import os
import time

import netcfg_vault.license as lic

PRIV = open(os.environ["NETCFG_SIGNING_KEY_PATH"]).read()


def _gen_v2(customer="acme", limit=50, days=365):
    return lic.generate_license_v2(customer, limit, days, private_key_pem=PRIV)


def test_v2_roundtrip():
    key = _gen_v2()
    assert key.startswith("NCVE-")
    info = lic.load_license_from(key)
    assert info is not None and info["version"] == 2
    assert info["customer"] == "acme"
    assert info["device_limit"] == 50


def test_v2_tamper_rejected():
    key = _gen_v2()
    body = key[5:]
    flipped = ("B" if body[0] != "B" else "C") + body[1:]
    assert lic.load_license_from("NCVE-" + flipped) is None


def test_v2_expiry_enforced():
    key = _gen_v2(days=-1)
    assert lic.load_license_from(key) is None


def test_v2_env_load(monkeypatch):
    key = _gen_v2("corp", 100)
    monkeypatch.setenv("NETCFG_LICENSE", key)
    assert lic.effective_device_limit() == 100


def test_v1_still_valid():
    key = lic.generate_license("legacy", 20)
    info = lic.load_license_from(key)
    assert info is not None and info["version"] == 1 and info["customer"] == "legacy"
