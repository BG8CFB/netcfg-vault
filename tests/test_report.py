import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from netcfg_vault.report import generate_report

TMP = Path(__file__).parent / "_report_tmp"


def _make(cfgs: dict, prev: dict | None = None):
    shutil.rmtree(TMP, ignore_errors=True)
    cur = TMP / "cur"; cur.mkdir(parents=True)
    for name, body in cfgs.items():
        (cur / name).write_text(body, encoding="utf-8")
    if prev:
        pv = TMP / "prev"; pv.mkdir()
        for name, body in prev.items():
            (pv / name).write_text(body, encoding="utf-8")
        return cur, pv
    return cur, None


def test_report_with_findings_and_diff():
    cur, prev = _make(
        {"sw1.cfg": "telnet server enable\nport x\n", "sw2.cfg": "ssh server enable\n"},
        {"sw1.cfg": "port x\n", "sw2.cfg": "ssh server enable\n"},
    )
    out = generate_report(cur, TMP / "r.html", prev_dir=prev)
    page = out.read_text(encoding="utf-8")
    assert "巡检报告" in page and "telnet 管理已开启" in page
    assert "有变更" in page and "无变更" in page


def test_report_clean():
    cur, _ = _make({"sw9.cfg": "ssh server enable\n"})
    out = generate_report(cur, TMP / "r2.html")
    assert "全部设备通过" in out.read_text(encoding="utf-8")


def teardown_module(module):
    shutil.rmtree(TMP, ignore_errors=True)
