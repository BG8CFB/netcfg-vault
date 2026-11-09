"""Tests for the config-diff engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from netcfg_vault.diff import changed_lines, diff_configs, normalize

OLD = """#
version 7.1.075, ESS 1110
# Last modified at 09:12:34 UTC Mon 11/09/2026
sysname CoreSW01
vlan 10
 description office
interface GigabitEthernet1/0/1
 port link-type trunk
return
"""

NEW_SAME = """#
version 7.1.075, ESS 1110
# Last modified at 18:45:00 UTC Mon 11/09/2026
sysname CoreSW01
vlan 10
 description office
interface GigabitEthernet1/0/1
 port link-type trunk
return
"""

NEW_CHANGED = """#
version 7.1.075, ESS 1110
sysname CoreSW02
vlan 10
 description office-new
interface GigabitEthernet1/0/1
 port link-type access
return
"""


def test_normalize_strips_timestamp():
    assert "# Last modified" not in "\n".join(normalize(OLD))


def test_no_change_after_noise_removal():
    a, r = changed_lines(OLD, NEW_SAME)
    assert (a, r) == (0, 0), f"expected no effective change, got +{a}/-{r}"


def test_change_detected_and_counted():
    a, r = changed_lines(OLD, NEW_CHANGED)
    assert a >= 3 and r >= 3, f"expected >=3 added and removed, got +{a}/-{r}"


def test_diff_contains_changed_sysname():
    out = diff_configs(OLD, NEW_CHANGED)
    assert "-sysname CoreSW01" in out
    assert "+sysname CoreSW02" in out
