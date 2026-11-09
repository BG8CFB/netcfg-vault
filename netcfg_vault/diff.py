"""Config diff engine: normalize vendor noise, produce unified diffs."""
import difflib
import re

# 这些行每次读取都会变化（时间戳/uptime），对比前剔除，否则全是假差异
NOISE_PATTERNS = [
    re.compile(r"^!.*Time.*$", re.IGNORECASE),
    re.compile(r"^#\s*Last\s+modified.*$", re.IGNORECASE),       # h3c
    re.compile(r"^#\s*\d{4}-\d{2}-\d{2}.*$", re.IGNORECASE),   # huawei 时间戳行
    re.compile(r"^\s*Building configuration.*$", re.IGNORECASE),
    re.compile(r"^Current configuration.*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s+(second|minute|hour|day)s?[,\s]", re.IGNORECASE),
]


def normalize(text):
    """Strip volatile lines (timestamps, sizes) so diffs show real changes only."""
    kept = []
    for line in text.splitlines():
        if any(p.match(line) for p in NOISE_PATTERNS):
            continue
        kept.append(line.rstrip())
    return kept


def diff_configs(old_text, new_text):
    """Return unified-diff string; empty string when no effective change."""
    old, new = normalize(old_text), normalize(new_text)
    delta = list(difflib.unified_diff(old, new, fromfile="previous", tofile="current", lineterm=""))
    return "\n".join(delta)


def changed_lines(old_text, new_text):
    """Return (added, removed) line counts after normalization."""
    old, new = normalize(old_text), normalize(new_text)
    sm = difflib.SequenceMatcher(a=old, b=new)
    added = sum(j - i for _tag, _i1, _i2, i, j in sm.get_opcodes() if _tag in ("insert", "replace"))
    removed = sum(i2 - i1 for _tag, i1, i2, _i, _j in sm.get_opcodes() if _tag in ("delete", "replace"))
    return added, removed
