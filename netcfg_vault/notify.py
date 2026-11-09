"""备份失败告警通道（Pro 功能）。

输入: 字符串列表 messages。
输出: 通过配置的 webhook（钉钉/企业微信/飞书/Server酱）发送 POST；无配置时退化为 stderr 打印。
失败条件: webhook 返回非 200 或网络异常——告警失败不应中断备份主流程，异常被吞并记录。
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request


def stderr_notify(messages):
    """默认通道: 打印到 stderr。"""
    for m in messages:
        print(f"[notify] {m}", file=sys.stderr)


def make_webhook_notify(url):
    """构造向群机器人 webhook 发文本的告警函数。

    自动识别钉钉/企业微信/飞书/Server酱 的 payload 格式。
    """
    def notify(messages):
        text = "\n".join(f"[netcfg-vault] {m}" for m in messages)
        if "oapi.dingtalk.com" in url:
            payload = {"msgtype": "text", "text": {"content": text}}
        elif "qyapi.weixin.qq.com" in url:
            payload = {"msgtype": "text", "text": {"content": text}}
        elif "open.feishu.cn" in url:
            payload = {"msg_type": "text", "content": {"text": text}}
        else:
            payload = {"title": "netcfg-vault 备份告警", "desp": text}
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as exc:  # noqa: BLE001 - 告警失败不中断备份
            print(f"[notify-error] webhook 发送失败: {exc}", file=sys.stderr)

    return notify


def get_notify():
    """从环境变量 NETCFG_WEBHOOK 读取 webhook URL 构造告警函数。"""
    url = os.environ.get("NETCFG_WEBHOOK")
    return make_webhook_notify(url) if url else stderr_notify
