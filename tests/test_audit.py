import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from netcfg_vault.audit import audit_dir

TMP = Path(__file__).parent / "_audit_tmp"


def _make_cfg(name: str, body: str) -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(exist_ok=True)
    (TMP / name).write_text(body, encoding="utf-8")


def test_audit_finds_risky_config():
    _make_cfg("sw1.cfg", "telnet server enable\nsnmp-agent community read public\nuser-interface vty 0 4\n")
    f = audit_dir(TMP)
    ids = {x.rule_id for x in f}
    assert "telnet-enabled" in ids and "snmp-default" in ids and "vty-no-acl" in ids


def test_audit_clean_config():
    _make_cfg("sw2.cfg", "ssh server enable\nuser-interface vty 0 4\n acl 2000 inbound\n")
    ids = {x.rule_id for x in audit_dir(TMP)}
    assert ids == set()


def teardown_module(module):
    import shutil
    shutil.rmtree(TMP, ignore_errors=True)
