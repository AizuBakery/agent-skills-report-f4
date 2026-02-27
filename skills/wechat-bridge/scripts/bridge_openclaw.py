#!/usr/bin/env python3
"""
微信 ↔ OpenClaw Agent 桥接器

与 bridge.py（硬编码流程）的区别：
  - bridge.py:          parse_command() → 直接 subprocess 调用脚本
  - bridge_openclaw.py: 原样转发消息 → OpenClaw Agent (Kimi K2.5) 理解意图 → 自动匹配 skill → 执行

用法:
  python3 bridge_openclaw.py --chat your_contact --interval 30
  python3 bridge_openclaw.py --chat your_contact --once          # 单次检测
  python3 bridge_openclaw.py --chat your_contact --test "处理照片"  # 直接测试，不轮询
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# wechat_mcp for reliable message sending (open once, send many)
_venv_sp = os.path.expanduser("~/wechat-integration/wechat-mcp-venv/lib/python3.14/site-packages")
if _venv_sp not in sys.path:
    sys.path.insert(0, _venv_sp)

WECHAT_CLI = os.path.expanduser("~/wechat-integration/wechat")
STATE_FILE = "/tmp/wechat_bridge_openclaw_state.json"
LOG_FILE = "/tmp/wechat_bridge_openclaw.log"

# ── Logging ─────────���─────────────────────────────────────

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


# ── WeChat I/O ────────────────────────────────────────────

_chat_opened = False
_current_chat = None


def open_chat_once(chat_name: str):
    """只在第一次（或切换聊天时）打开聊天窗口。"""
    global _chat_opened, _current_chat
    if not _chat_opened or _current_chat != chat_name:
        from wechat_mcp.wechat_keyboard import open_chat_via_keyboard
        open_chat_via_keyboard(chat_name)
        time.sleep(0.5)
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to key code 53'], timeout=5)
        time.sleep(0.3)
        _chat_opened = True
        _current_chat = chat_name


def send_wechat(chat_name: str, msg: str):
    """发送微信消息（复用已打开的聊天窗口）。"""
    from wechat_mcp.wechat_keyboard import _activate_wechat, _set_clipboard, _run_applescript
    log(f"[微信→] {msg[:60]}...")
    open_chat_once(chat_name)
    _activate_wechat()
    time.sleep(0.2)
    _set_clipboard(msg)
    _run_applescript(
        'tell application "System Events" to tell process "WeChat" '
        'to keystroke "v" using command down'
    )
    time.sleep(0.3)
    _run_applescript(
        'tell application "System Events" to tell process "WeChat" '
        'to key code 36'
    )
    time.sleep(0.5)


def read_chat(chat_name: str) -> list[str]:
    """通过 wechat CLI 读取聊天记录。"""
    try:
        result = subprocess.run(
            [WECHAT_CLI, "chat", chat_name],
            capture_output=True, text=True, timeout=30
        )
        messages = []
        for line in result.stdout.strip().split("\n"):
            if "[左" in line or "[右" in line:
                parts = line.split("] ", 1)
                if len(parts) == 2:
                    messages.append(parts[1].strip())
        return messages
    except Exception as e:
        log(f"读取聊天失败: {e}")
        return []


# ── OpenClaw Agent ────────────────────────────────────────

def call_openclaw_agent(message: str, timeout: int = 600) -> str | None:
    """调用 OpenClaw Agent 处理消息，返回 agent 的回复文本。"""
    log(f"[OpenClaw] 发送给 Agent: {message[:80]}...")
    try:
        # 继承当前 shell 环境（含 ZENMUX_API_KEY 等），gateway LaunchAgent 可能缺失这些
        env = os.environ.copy()
        result = subprocess.run(
            ["openclaw", "agent", "--agent", "main",
             "--message", message,
             "--json", "--timeout", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 30,
            env=env
        )
        if result.returncode != 0:
            log(f"[OpenClaw] Agent 返回错误: {result.stderr[:200]}")
            return f"Agent 执行出错: {result.stderr[:200]}"

        data = json.loads(result.stdout)
        # gateway 模式: result.payloads[].text
        payloads = data.get("result", data).get("payloads", [])
        texts = [p["text"] for p in payloads if p.get("text")]
        if texts:
            reply = "\n".join(texts)
            log(f"[OpenClaw] Agent 回复: {reply[:100]}...")
            return reply

        log("[OpenClaw] Agent 无文本回复")
        return "Agent 处理完成，但没有返回文本。"

    except subprocess.TimeoutExpired:
        log("[OpenClaw] Agent 超时")
        return "Agent 执行超时。"
    except json.JSONDecodeError as e:
        log(f"[OpenClaw] JSON 解析失败: {e}")
        return f"Agent 返回格式异常。"
    except Exception as e:
        log(f"[OpenClaw] 调用失败: {e}")
        return f"Agent 调用失败: {e}"


# ── State Management ──────────────────────────────────────

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


# ── Message Filter ────────────────────────────────────────

def is_actionable(msg: str) -> bool:
    """判断消息是否值得交给 Agent 处理（过滤噪音）。"""
    msg = msg.strip()
    if len(msg) < 2:
        return False
    # 过滤常见的非指令消息
    noise = {"你好", "好的", "谢谢", "ok", "OK", "嗯", "哦", "收到"}
    if msg in noise:
        return False
    # 过滤 agent 自己的回复（避免循环）
    if msg.startswith(("Agent ", "[OpenClaw]", "收到指令", "执行完成", "执行失败")):
        return False
    return True


# ── Main Loop ─────────────────────────────────────────────

def poll_loop(chat_name: str, interval: int, once: bool = False):
    log(f"启动 OpenClaw 桥接器: 监听={chat_name}, 间隔={interval}秒")
    state = load_state()

    while True:
        try:
            messages = read_chat(chat_name)
            current_hash = messages_hash(messages)

            if current_hash != state["last_hash"] and messages:
                latest = messages[-1]
                log(f"消息变化: latest=[{latest}]")

                if is_actionable(latest) and latest not in state["processed"]:
                    log(f"检测到新指令: {latest}")

                    # 先回复确认
                    send_wechat(chat_name, f"收到，正在处理: {latest[:50]}...")

                    # 交给 OpenClaw Agent
                    reply = call_openclaw_agent(latest)

                    # 发送 Agent 回复
                    if reply:
                        # 分段发送（微信单条消息不宜过长）
                        chunks = split_message(reply, max_len=500)
                        for chunk in chunks:
                            send_wechat(chat_name, chunk)
                            if len(chunks) > 1:
                                time.sleep(1)

                    state["processed"].append(latest)
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


def split_message(text: str, max_len: int = 500) -> list[str]:
    """按段落拆分长消息。"""
    if len(text) <= max_len:
        return [text]

    chunks = []
    current = ""
    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_len and current:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks or [text[:max_len]]


def test_mode(chat_name: str, message: str):
    """直接测试模式：跳过轮询，直接发送消息给 Agent 并回复。"""
    log(f"测试模式: chat={chat_name}, message={message}")
    send_wechat(chat_name, f"收到，正在处理: {message[:50]}...")
    reply = call_openclaw_agent(message)
    if reply:
        chunks = split_message(reply, max_len=500)
        for chunk in chunks:
            send_wechat(chat_name, chunk)
            if len(chunks) > 1:
                time.sleep(1)
    log("测试完成")


def main():
    parser = argparse.ArgumentParser(description="微信 ↔ OpenClaw Agent 桥接器")
    parser.add_argument("--chat", required=True, help="监听的聊天名称")
    parser.add_argument("--interval", type=int, default=30, help="轮询间隔秒数（默认30）")
    parser.add_argument("--once", action="store_true", help="只检查一次")
    parser.add_argument("--test", metavar="MSG", help="测试模式：直接发送消息给 Agent")
    parser.add_argument("--reset", action="store_true", help="重置状态")
    args = parser.parse_args()

    if args.reset:
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
        log("状态已重置")

    if args.test:
        test_mode(args.chat, args.test)
    else:
        poll_loop(args.chat, args.interval, args.once)


if __name__ == "__main__":
    main()
