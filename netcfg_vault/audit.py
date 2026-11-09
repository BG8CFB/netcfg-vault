"""Configuration compliance audit over saved backup files.

Input: a directory of device config backups produced by netcfg-vault backup.
Output: per-device findings (CSV or stdout), sorted by severity.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

RULES = [
    {
        "id": "telnet-enabled",
        "desc": "telnet 管理已开启",
        "severity": "high",
        "test": lambda cfg: bool(re.search(r"^\s*telnet server enable", cfg, re.M)),
    },
    {
        "id": "snmp-default",
        "desc": "SNMP 使用默认团体名 public/private",
        "severity": "high",
        "test": lambda cfg: bool(re.search(r"snmp-agent community (?:read|write) (?:public|private)", cfg, re.I) or re.search(r"snmp-server community (?:public|private)", cfg, re.I)),
    },
    {
        "id": "http-enabled",
        "desc": "设备 Web 管理已开启",
        "severity": "medium",
        "test": lambda cfg: bool(re.search(r"^\s*(?:ip http enable|undo ip http disable|ip http server)$", cfg, re.M)),
    },
    {
        "id": "ssh-v1",
        "desc": "SSH v1 兼容模式",
        "severity": "medium",
        "test": lambda cfg: bool(re.search(r"ssh server compatible-ssh1x enable", cfg, re.I) or re.search(r"ip ssh version 1", cfg, re.I)),
    },
    {
        "id": "weak-password",
        "desc": "本地用户密码为 simple/明文",
        "severity": "high",
        "test": lambda cfg: bool(re.search(r"password (?:simple|cipher) (?:\w{1,7})\s*$", cfg, re.M | re.I)),
    },
    {
        "id": "vty-no-acl",
        "desc": "VTY 线路未绑定 ACL",
        "severity": "medium",
        "test": lambda cfg: (bool(re.search(r"user-interface vty", cfg, re.I)) and not re.search(r"vty[\s\S]*?acl \d+ inbound", cfg, re.I)),
    },
]


@dataclass
class Finding:
    device: str
    rule_id: str
    desc: str
    severity: str


def audit_dir(cfg_dir: str | Path) -> list[Finding]:
    """Audit every config file in cfg_dir. Returns findings sorted high→low."""
    findings: list[Finding] = []
    for p in sorted(Path(cfg_dir).iterdir()):
        if not p.is_file():
            continue
        cfg = p.read_text(encoding="utf-8", errors="ignore")
        for rule in RULES:
            if rule["test"](cfg):
                findings.append(Finding(device=p.name, rule_id=rule["id"], desc=rule["desc"], severity=rule["severity"]))
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.device))
    return findings


def write_csv(findings: list[Finding], out: str | Path) -> None:
    with open(out, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["device", "rule_id", "desc", "severity"])
        for f in findings:
            w.writerow([f.device, f.rule_id, f.desc, f.severity])
