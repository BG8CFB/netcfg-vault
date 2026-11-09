"""Baseline snapshots: lock a backup directory as a reference point,
then diff future backups against it.

Layout: <work>/.netcfg-baselines/<name>/<files> + manifest.json
Operations: set / list / diff / remove. Pure stdlib; reuses diff_configs.
"""
from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

from .diff import diff_configs

BASELINE_ROOT = ".netcfg-baselines"
CONFIG_EXT = {".cfg", ".config", ".txt", ".log"}


def _root() -> Path:
    return Path.cwd() / BASELINE_ROOT


def _iter_configs(d: Path):
    if not d.is_dir():
        return
    for p in sorted(d.rglob("*")):
        if p.is_file() and p.suffix.lower() in CONFIG_EXT:
            yield p


def _read(p: Path) -> str:
    for enc in ("utf-8", "gbk", "latin-1"):
        try:
            return p.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return p.read_text(encoding="utf-8", errors="replace")


def cmd_set(src: str, name: str) -> int:
    srcd = Path(src)
    if not srcd.is_dir():
        print(f"err: directory not found: {src}", file=sys.stderr)
        return 2
    dest = _root() / name
    if dest.exists():
        print(f"err: baseline exists: {name} (remove first)", file=sys.stderr)
        return 2
    files = list(_iter_configs(srcd))
    if not files:
        print("err: no config files found (.cfg/.config/.txt/.log)", file=sys.stderr)
        return 2
    dest.mkdir(parents=True)
    copied = 0
    for p in files:
        rel = p.relative_to(srcd)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, target)
        copied += 1
    manifest = {
        "name": name,
        "source": str(srcd),
        "created": datetime.now().isoformat(timespec="seconds"),
        "files": copied,
    }
    (dest / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"baseline [{name}] saved: {copied} files from {src}")
    return 0


def cmd_list() -> int:
    root = _root()
    if not root.is_dir():
        print("no baselines (run: netcfg-vault baseline set <dir> --name <n>)")
        return 0
    found = False
    for mf in sorted(root.glob("*/manifest.json")):
        m = json.loads(mf.read_text(encoding="utf-8"))
        print("  %-16s %s  %s files  <- %s" % (m["name"], m["created"], m["files"], m["source"]))
        found = True
    if not found:
        print("no baselines")
    return 0


def cmd_diff(cur: str, name: str) -> int:
    based = _root() / name
    if not (based / "manifest.json").exists():
        print(f"err: baseline not found: {name}", file=sys.stderr)
        return 2
    curd = Path(cur)
    if not curd.is_dir():
        print(f"err: directory not found: {cur}", file=sys.stderr)
        return 2
    base_files = {p.relative_to(based).as_posix(): _read(p) for p in _iter_configs(based)}
    cur_files = {p.relative_to(curd).as_posix(): _read(p) for p in _iter_configs(curd)}
    changed = 0
    for rel in sorted(set(base_files) | set(cur_files)):
        b = base_files.get(rel)
        c = cur_files.get(rel)
        if b is None:
            print("+ NEW      " + rel)
            changed += 1
            continue
        if c is None:
            print("- MISSING  " + rel)
            changed += 1
            continue
        d = diff_configs(b, c)
        if d.strip():
            changed += 1
            print("~ CHANGED  " + rel)
            lines = d.splitlines()
            for line in lines[:20]:
                print("    " + line)
            if len(lines) > 20:
                print("    ... (%d more lines)" % (len(lines) - 20))
    if not changed:
        print("identical to baseline")
    else:
        print("%d file(s) differ from baseline [%s]" % (changed, name))
    return 1 if changed else 0


def cmd_remove(name: str) -> int:
    dest = _root() / name
    if not dest.is_dir():
        print(f"err: baseline not found: {name}", file=sys.stderr)
        return 2
    shutil.rmtree(dest)
    print(f"baseline [{name}] removed")
    return 0


def main() -> int:
    argv = sys.argv[2:] if len(sys.argv) > 1 else []
    if argv[:1] == ["set"]:
        if len(argv) < 4 or argv[2] != "--name":
            print("usage: netcfg-vault baseline set <dir> --name <name>")
            return 2
        return cmd_set(argv[1], argv[3])
    if argv[:1] == ["list"]:
        return cmd_list()
    if argv[:1] == ["diff"]:
        if len(argv) < 4 or argv[2] != "--name":
            print("usage: netcfg-vault baseline diff <dir> --name <name>")
            return 2
        return cmd_diff(argv[1], argv[3])
    if argv[:1] == ["remove"]:
        if len(argv) < 2:
            print("usage: netcfg-vault baseline remove <name>")
            return 2
        return cmd_remove(argv[1])
    print("usage: netcfg-vault baseline {set|list|diff|remove} ...")
    return 2
