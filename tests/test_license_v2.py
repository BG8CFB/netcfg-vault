"""v2 Ed25519 license 测试。

需要作者侧私钥(NETCFG_SIGNING_KEY_PATH 指向 PEM)。无私钥环境(如 CI)自动跳过
签名相关用例, 只验证 key 解析/拒绝路径。
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest  # noqa: E402

import netcfg_vault.license as lic  # noqa: E402

PRIV_PATH = os.environ.get("NETCFG_SIGNING_KEY_PATH", "")
PRIV = open(PRIV_PATH).read() if PRIV_PATH else None

needs_key = pytest.mark.skipif(PRIV is None, reason="NETCFG_SIGNING_KEY_PATH not set")


@needs_key
def test_generate_v2_and_verify():
    key = lic.generate_license_v2("acme", 50, 365, private_key_pem=PRIV)
    assert key.startswith("NCVE-")
    info = lic.load_license_from(key)
    assert info is not None
    assert info["customer"] == "acme"
    assert info["device_limit"] == 50
    assert info["version"] == 2


@needs_key
def test_v2_rejects_tampered_key():
    key = lic.generate_license_v2("acme", 50, 365, private_key_pem=PRIV)
    body = key[5:]
    flipped = ("B" if body[0] != "B" else "C") + body[1:]
    assert lic.load_license_from("NCVE-" + flipped) is None


def test_v2_rejects_garbage():
    assert lic.load_license_from("NCVE-AAAA") is None
    assert lic.load_license_from("not-a-key") is None


def test_load_license_from_v1_still_works():
    """v1 HMAC key 继续可用(向后兼容)。"""
    key = lic.generate_license("legacy-corp", 20, 365)
    info = lic.load_license_from(key)
    assert info is not None
    assert info["customer"] == "legacy-corp"
    assert info["device_limit"] == 20
