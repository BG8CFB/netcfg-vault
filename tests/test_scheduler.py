import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import netcfg_vault.scheduler as sch
from netcfg_vault.scheduler import Scheduler

inv = tempfile.mkdtemp()
dev_path = os.path.join(inv, 'devices.yml')
open(dev_path, 'w', encoding='utf-8').write('devices:\n  - name: fake1\n    host: 1.1.1.1\n    vendor: h3c\n    protocol: ssh\n    username: a\n')

calls = []
def fake_backup(dev, ask_pass=False):
    calls.append(dev['name'])
    if dev['name'] == 'bad':
        raise RuntimeError('conn refused')
    return 'sysname FAKE\n'

sch.backup_device = fake_backup
notified = []
out = tempfile.mkdtemp()
s = Scheduler(dev_path, out, interval=1, notify=notified.extend)
ok, failed = s.run_once()
assert ok == 1 and failed == [] and calls == ['fake1'], (ok, failed, calls)
open(dev_path, 'a', encoding='utf-8').write('  - name: bad\n    host: 2.2.2.2\n    vendor: h3c\n    protocol: ssh\n    username: a\n')
ok2, failed2 = s.run_once()
assert ok2 == 1 and len(failed2) == 1 and 'bad: conn refused' in failed2[0], (ok2, failed2)
assert notified and 'bad: conn refused' in notified[0], notified
stamp_dirs = os.listdir(out)
assert len(stamp_dirs) == 1, stamp_dirs
files = os.listdir(os.path.join(out, stamp_dirs[0]))
assert 'fake1.cfg' in files, files
print('SCHED TESTS PASS ok=%d failed=%s files=%s' % (ok2, failed2, files))