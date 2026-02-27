#!/usr/bin/env python3
"""
微信消息轮询桥接器 — 监听微信聊天中的指令，转发给 OpenClaw agent 执行。

用法:
  python3 bridge.py --chat "文件传输助手" --interval 30
  python3 bridge.py --chat "your_contact" --interval 15 --once

支持的指令（在微信聊天中发送）:
  处理图片         → 触发 auto-twitter-campaign 完整流水线
  处理图片 xxx.jpg → 处理指定图片
  生成推文         → 从已有对比图生成推文文案
  生成图片 <描述>  → AI 文生图
  修图 <描述>      → 编辑最近一张图片
  发公众号 <标题>  → 触发公众号发布流程
  状态             → 报告当前系统状态
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

WECHAT_CLI = os.path.expanduser("~/wechat-integration/wechat")
STATE_FILE = "/tmp/wechat_bridge_state.json"
LOG_FILE = "/tmp/wechat_bridge.log"


def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def read_chat(chat_name: str) -> list[str]:
    """通过 wechat CLI 读取聊天记录，返回所有消息（左=对方，右=自己）。"""
    try:
        result = subprocess.run(
            [WECHAT_CLI, "chat", chat_name],
            capture_output=True, text=True, timeout=30
        )
        lines = result.stdout.strip().split("\n")
        # 提取左侧和右侧消息（跳过中间的时间戳）
        messages = []
        for line in lines:
            if "[左" in line or "[右" in line:
                # 格式: [左/右 0.xx] 消息内容
                parts = line.split("] ", 1)
                if len(parts) == 2:
                    messages.append(parts[1].strip())
        return messages
    except Exception as e:
        log(f"读取聊天失败: {e}")
        return []


def send_reply(chat_name: str, msg: str):
    """通过 wechat CLI 发送回复。"""
    try:
        subprocess.run(
            [WECHAT_CLI, "send", chat_name, msg],
            timeout=15
        )
    except Exception as e:
        log(f"发送回复失败: {e}")


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_hash": "", "processed": []}


def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def messages_hash(messages: list[str]) -> str:
    return hashlib.md5("|".join(messages[-5:]).encode()).hexdigest()


def parse_command(msg: str) -> tuple[str, str] | None:
    """解析微信消息中的指令，返回 (action, args) 或 None。"""
    msg = msg.strip()

    # 精确匹配
    if msg in ("处理图片", "跑流水线", "run"):
        return ("campaign_run", "")
    if msg in ("生成推文", "写推文", "推文"):
        return ("campaign_showcase", "")
    if msg in ("状态", "status"):
        return ("status", "")

    # 前缀匹配 — 用字典简化，(前缀列表, action)
    prefix_rules = [
        (["处理图片 ", "处理 "], "campaign_process"),
        (["生成推文 ", "写推文 "], "campaign_showcase"),
        (["生成图片 ", "生成 ", "画 "], "generate_image"),
        (["修图 ", "编辑图片 ", "编辑 "], "edit_image"),
        (["发公众号 ", "公众号 "], "publish_wechat"),
    ]

    for prefixes, action in prefix_rules:
        for prefix in prefixes:
            if msg.startswith(prefix):
                return (action, msg[len(prefix):].strip())

    return None


def execute_command(action: str, args: str, chat_name: str):
    """执行指令并回复结果。"""
    log(f"执行指令: action={action}, args={args}")
    send_reply(chat_name, f"收到指令 [{action}]，开始执行...")

    try:
        if action == "status":
            # 检查各组件状态
            pending = list(Path.home().glob("campaign_images/pending/*"))
            results = list(Path.home().glob("campaign_images/results/compare_*"))
            send_reply(chat_name, f"系统状态:\n待处理图片: {len(pending)}\n已完成对比图: {len(results)}")
            return

        if action == "campaign_run":
            result = subprocess.run(
                ["python3", os.path.expanduser("~/.openclaw/workspace/skills/auto-twitter-campaign/scripts/campaign.py"), "run"],
                capture_output=True, text=True, timeout=600
            )
        elif action == "campaign_process":
            cmd = ["python3", os.path.expanduser("~/.openclaw/workspace/skills/auto-twitter-campaign/scripts/campaign.py"), "process"]
            if args:
                cmd.extend(["--image", args])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        elif action == "campaign_showcase":
            cmd = ["python3", os.path.expanduser("~/.openclaw/workspace/skills/auto-twitter-campaign/scripts/campaign.py"), "showcase"]
            if args:
                cmd.extend(["--description", args])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        elif action == "generate_image":
            result = subprocess.run(
                ["python3", os.path.expanduser("~/.openclaw/workspace/skills/ming-flash-omni/scripts/ming_image.py"), "generate", args],
                capture_output=True, text=True, timeout=120
            )
        elif action == "edit_image":
            # 找最近一张 pending 图片
            pending = sorted(Path.home().glob("campaign_images/pending/*"), key=os.path.getmtime, reverse=True)
            if not pending:
                send_reply(chat_name, "没有找到待编辑的图片")
                return
            result = subprocess.run(
                ["python3", os.path.expanduser("~/.openclaw/workspace/skills/ming-flash-omni/scripts/ming_image.py"), "edit", str(pending[0]), args],
                capture_output=True, text=True, timeout=120
            )
        elif action == "publish_wechat":
            # 通过 openclaw agent 触发，让 agent 智能处理
            result = subprocess.run(
                ["openclaw", "agent", "--local", "--message", f"发布公众号文章，标题：{args}"],
                capture_output=True, text=True, timeout=300
            )
        else:
            send_reply(chat_name, f"未知指令: {action}")
            return

        # 提取关键输出
        output = result.stdout.strip()
        if result.returncode == 0:
            # 截取最后几行作为摘要
            lines = output.split("\n")
            summary = "\n".join(lines[-5:]) if len(lines) > 5 else output
            send_reply(chat_name, f"执行完成:\n{summary}")
        else:
            error = result.stderr.strip()[-200:] if result.stderr else "未知错误"
            send_reply(chat_name, f"执行失败:\n{error}")

    except subprocess.TimeoutExpired:
        send_reply(chat_name, "执行超时，请检查任务状态")
    except Exception as e:
        send_reply(chat_name, f"执行出错: {e}")


def poll_loop(chat_name: str, interval: int, once: bool = False):
    """主轮询循环。"""
    log(f"启动微信桥接器: 监听聊天={chat_name}, 间隔={interval}秒")
    state = load_state()

    while True:
        try:
            messages = read_chat(chat_name)
            current_hash = messages_hash(messages)
            log(f"轮询: 读到{len(messages)}条消息, hash={current_hash[:8]}, 最新=[{messages[-1] if messages else ''}]")

            if current_hash != state["last_hash"] and messages:
                # 消息有变化，检查最新消息是否是指令
                latest = messages[-1]
                cmd = parse_command(latest)
                log(f"消息变化: latest=[{latest}], 指令匹配={cmd}")

                if cmd and latest not in state["processed"]:
                    action, args = cmd
                    log(f"检测到新指令: {latest}")
                    execute_command(action, args, chat_name)
                    state["processed"].append(latest)
                    # 只保留最近20条已处理记录
                    state["processed"] = state["processed"][-20:]

                state["last_hash"] = current_hash
                save_state(state)

        except KeyboardInterrupt:
            log("桥接器停止")
            break
        except Exception as e:
            log(f"轮询出错: {e}")

        if once:
            break

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="微信消息轮询桥接器")
    parser.add_argument("--chat", required=True, help="监听的聊天名称（如：文件传输助手）")
    parser.add_argument("--interval", type=int, default=30, help="轮询间隔秒数（默认30）")
    parser.add_argument("--once", action="store_true", help="只检查一次然后退出")
    parser.add_argument("--reset", action="store_true", help="重置状态文件")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        log("状态已重置")

    poll_loop(args.chat, args.interval, args.once)


if __name__ == "__main__":
    main()
