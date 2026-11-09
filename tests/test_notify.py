import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from netcfg_vault.notify import make_webhook_notify, get_notify, stderr_notify

# 无环境变量时退化为 stderr 通道
os.environ.pop('NETCFG_WEBHOOK', None)
assert get_notify() is stderr_notify

# webhook 通道构造不触发网络（只在调用时发）
n = make_webhook_notify('https://oapi.dingtalk.com/robot/send?access_token=x')
assert callable(n)

# 发送失败被吞掉不抛异常
n(['unit-test failure'])
print('NOTIFY TESTS PASS')