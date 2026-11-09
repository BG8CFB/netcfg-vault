"""Inspection report generator: turns a backup directory into an HTML report.

Combines device inventory (from backup filenames), compliance findings
(audit rules) and optional day-over-day config diff stats into one
self-contained printable HTML file.
"""
from __future__ import annotations

import datetime as _dt
import html as _html
from pathlib import Path

from .audit import audit_dir
from .diff import diff_configs

_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>网络设备巡检报告 {date}</title>
<style>
 body{{font-family:"Microsoft YaHei",system-ui,sans-serif;margin:32px;color:#1a1a2e}}
 h1{{border-bottom:3px solid #2b6cb0;padding-bottom:8px}}
 .meta{{color:#555;margin-bottom:20px}}
 table{{border-collapse:collapse;width:100%;margin:12px 0}}
 th,td{{border:1px solid #cbd5e0;padding:6px 10px;text-align:left;font-size:14px}}
 th{{background:#edf2f7}}
 .high{{color:#c53030;font-weight:bold}}
 .medium{{color:#b7791f}}
 .low{{color:#4a5568}}
 .ok{{color:#2f855a}}
 .card{{background:#f7fafc;border-radius:8px;padding:14px 18px;margin:10px 0;display:inline-block;min-width:180px}}
 .num{{font-size:28px;font-weight:bold}}
 @media print{{.noprint{{display:none}}}}
</style>
</head>
<body>
<h1>网络设备巡检报告</h1>
<div class="meta">生成时间: {date} · 来源: netcfg-vault</div>
<div>
 <div class="card"><div class="num">{devices}</div>备份设备数</div>
 <div class="card"><div class="num">{high}</div>高危项</div>
 <div class="card"><div class="num">{medium}</div>中危项</div>
 <div class="card"><div class="num">{changed}</div>配置变更设备</div>
</div>
<h2>合规审计明细</h2>
{findings}
<h2>配置变更</h2>
{changes}
<p class="noprint" style="margin-top:30px;color:#888">由 netcfg-vault 自动生成 · github.com/BG8CFB/netcfg-vault</p>
</body></html>"""


def _device_name(fname: str) -> str:
    return Path(fname).stem


def generate_report(cfg_dir: str | Path, out: str | Path, prev_dir: str | Path | None = None) -> Path:
    """Generate HTML inspection report from cfg_dir; if prev_dir given, diff device configs day-over-day."""
    cfg_dir = Path(cfg_dir)
    findings = audit_dir(cfg_dir)
    devices = sorted(p.name for p in cfg_dir.iterdir() if p.is_file())

    high = sum(1 for f in findings if f.severity == "high")
    medium = sum(1 for f in findings if f.severity == "medium")

    change_rows = []
    changed_count = 0
    if prev_dir:
        prev_dir = Path(prev_dir)
        for name in devices:
            prev = prev_dir / name
            cur = cfg_dir / name
            if not prev.exists():
                change_rows.append('<tr><td>%s</td><td>新设备/无昨日备份</td><td>-</td></tr>' % _html.escape(_device_name(name)))
                continue
            d = diff_configs(prev.read_text(encoding="utf-8", errors="ignore"), cur.read_text(encoding="utf-8", errors="ignore")).splitlines()
            n = sum(1 for line in d if line.startswith("+") and not line.startswith("+++")) - sum(1 for line in d if line.startswith("-") and not line.startswith("---"))
            if n != 0:
                changed_count += 1
                sign = '+' if n > 0 else ''
                cls = 'high' if abs(n) > 20 else 'medium'
                state = '有变更' if n else '无变更'
                change_rows.append('<tr><td>%s</td><td>%s%d 行</td><td class="%s">%s</td></tr>' % (_html.escape(_device_name(name)), sign, n, cls, state))
            else:
                change_rows.append('<tr><td>%s</td><td>0 行</td><td class="ok">无变更</td></tr>' % _html.escape(_device_name(name)))

    if findings:
        f_rows = ""
        for f in findings:
            f_rows += '<tr><td>%s</td><td>%s</td><td class=\"%s\">%s</td></tr>' % (_html.escape(f.device), _html.escape(f.desc), f.severity, f.severity.upper())
        findings_html = f"<table><tr><th>设备</th><th>问题</th><th>级别</th></tr>{f_rows}</table>"
    else:
        findings_html = '<p class="ok">全部设备通过 6 项合规检查, 无风险项。</p>'

    if change_rows:
        changes_html = "<table><tr><th>设备</th><th>变更量</th><th>状态</th></tr>" + "".join(change_rows) + "</table>"
    else:
        changes_html = "<p>未提供昨日目录, 跳过变更比对。使用 --prev 启用。</p>"

    page = _TEMPLATE.format(
        date=_dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        devices=len(devices),
        high=high,
        medium=medium,
        changed=changed_count,
        findings=findings_html,
        changes=changes_html,
    )
    out = Path(out)
    out.write_text(page, encoding="utf-8")
    return out
