"""vault 加密保管库测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from netcfg_vault.vault import vault_extract, vault_list, vault_save


def _make_tree(base: Path):
    d = base / "backups"
    (d / "2026-11-09").mkdir(parents=True)
    (d / "2026-11-09" / "core-sw-01.cfg").write_text("vlan 10\ninterface GE1/0/1")
    (d / "2026-11-09" / "core-sw-02.cfg").write_text("vlan 20")
    return d


def test_vault_roundtrip(tmp_path):
    src = _make_tree(tmp_path)
    vault = tmp_path / "b.nvault"
    n = vault_save(str(src), str(vault), "s3cret-pass")
    assert n == 2
    assert vault.read_bytes().startswith(b"NVAULT1")

    out = tmp_path / "restored"
    files = vault_extract(str(vault), "s3cret-pass", str(out))
    names = sorted(f["name"] for f in files)
    assert names == ["2026-11-09/core-sw-01.cfg", "2026-11-09/core-sw-02.cfg"]
    assert (out / "2026-11-09" / "core-sw-01.cfg").read_text() == "vlan 10\ninterface GE1/0/1"


def test_vault_wrong_passphrase(tmp_path):
    src = _make_tree(tmp_path)
    vault = tmp_path / "b.nvault"
    vault_save(str(src), str(vault), "right")
    try:
        vault_extract(str(vault), "wrong", str(tmp_path / "x"))
        raise AssertionError("wrong passphrase must fail")
    except Exception as exc:
        assert type(exc).__name__ == "InvalidTag"


def test_vault_list_no_write(tmp_path):
    src = _make_tree(tmp_path)
    vault = tmp_path / "b.nvault"
    vault_save(str(src), str(vault), "pw")
    files = vault_list(str(vault), "pw")
    assert len(files) == 2
    assert not (tmp_path / "restored").exists()
