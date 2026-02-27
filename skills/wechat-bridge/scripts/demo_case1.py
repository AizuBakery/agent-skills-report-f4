#!/usr/bin/env python3
"""
Case 1 Demo: 微信驱动的图片营销闭环

流程:
  1. 读取 your_contact 聊天记录，确认收到"处理照片"指令
  2. 回复"收到，开始处理..."
  3. 调用 auto-twitter-campaign 处理 pending/ 下的图片
  4. 生成对比图 + GIF + 推文文案
  5. 把结果汇报回 your_contact

用法:
  python3 demo_case1.py                    # 直接执行全流程
  python3 demo_case1.py --image xxx.jpg    # 只处理一张图
  python3 demo_case1.py --skip-process     # 跳过处理，只生成展示+推文
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# wechat_mcp lives in the wechat-integration venv
_venv_sp = os.path.expanduser("~/wechat-integration/wechat-mcp-venv/lib/python3.14/site-packages")
if _venv_sp not in sys.path:
    sys.path.insert(0, _venv_sp)

WECHAT_CLI = os.path.expanduser("~/wechat-integration/wechat")
CAMPAIGN_SCRIPT = os.path.expanduser("~/.openclaw/workspace/skills/auto-twitter-campaign/scripts/campaign.py")
CHAT_NAME = "your_contact"
PENDING_DIR = Path.home() / "campaign_images" / "pending"
RESULTS_DIR = Path.home() / "campaign_images" / "results"


_chat_opened = False

def open_chat_once():
    """只在第一次打开聊天窗口，之后复用"""
    global _chat_opened
    if not _chat_opened:
        from wechat_mcp.wechat_keyboard import open_chat_via_keyboard
        open_chat_via_keyboard(CHAT_NAME)
        time.sleep(0.5)
        # Escape 确保焦点离开搜索框
        subprocess.run(["osascript", "-e",
            'tell application "System Events" to key code 53'], timeout=5)
        time.sleep(0.3)
        _chat_opened = True


def send_in_current_chat(msg: str):
    """在已打开的聊天窗口中直接发送消息（不重新搜索）"""
    from wechat_mcp.wechat_keyboard import _activate_wechat, _set_clipboard, _run_applescript
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
    time.sleep(0.3)


def send(msg: str):
    """发送微信消息给 your_contact"""
    print(f"[微信] 发送: {msg[:50]}...")
    open_chat_once()
    send_in_current_chat(msg)
    time.sleep(1)


def count_files(directory: Path, pattern: str = "*") -> int:
    return len(list(directory.glob(pattern)))


def run_campaign(subcommand: str, extra_args: list[str] = None) -> tuple[int, str]:
    """运行 campaign 脚本"""
    cmd = ["python3", CAMPAIGN_SCRIPT, subcommand]
    if extra_args:
        cmd.extend(extra_args)
    print(f"[campaign] 执行: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return result.returncode, result.stdout + result.stderr


def main():
    parser = argparse.ArgumentParser(description="Case 1 Demo: 微信→处理照片→推文→微信回复")
    parser.add_argument("--image", help="只处理指定图片")
    parser.add_argument("--skip-process", action="store_true", help="跳过图片处理，直接生成展示")
    parser.add_argument("--dry-run", action="store_true", help="只打印流程，不实际执行")
    args = parser.parse_args()

    print("=" * 60)
    print("Case 1 Demo: 微信驱动的图片营销闭环")
    print("=" * 60)

    # Step 1: 确认状态
    pending_count = count_files(PENDING_DIR)
    existing_results = {p: p.stat().st_mtime for p in RESULTS_DIR.glob("compare_*")}
    print(f"\n[状态] pending/ 待处理: {pending_count} 张")
    print(f"[状态] results/ 已有对比图: {len(existing_results)} 张")

    if pending_count == 0 and not args.skip_process:
        print("[错误] pending/ 下没有待处理图片")
        sys.exit(1)

    if args.dry_run:
        print("\n[dry-run] 流程预览:")
        print("  1. 微信回复: 收到指令，开始处理...")
        print(f"  2. 处理 {pending_count} 张图片（AI清理+风格编辑）")
        print("  3. 生成对比图、GIF 展示")
        print("  4. AI 生成推文文案")
        print("  5. 微信回复: 处理完成 + 推文文案")
        return

    # Step 2: 微信回复确认
    if args.image:
        image_name = os.path.basename(args.image)
        send(f"收到指令：处理照片\n正在处理: {image_name}\n请稍候...")
    else:
        send(f"收到指令：处理照片\n待处理: {pending_count} 张图片\n开始AI清理+风格编辑，请稍候...")

    # Step 3+4: 处理图片 + 生成展示和推文（一次性执行，确保推文与本次图片匹配）
    if not args.skip_process:
        print("\n[Step 3+4] 处理图片 + 生成展示和推文...")
        extra = ["--image", args.image] if args.image else []
        code, output = run_campaign("run", extra)
        if code != 0:
            send(f"处理失败:\n{output[-200:]}")
            sys.exit(1)

        new_results = sum(1 for p in RESULTS_DIR.glob("compare_*")
                         if p not in existing_results or p.stat().st_mtime > existing_results[p])
        send(f"图片处理完成！新增 {new_results} 张对比图")
    else:
        print("\n[Step 4] 生成展示和推文...")
        code, output = run_campaign("showcase")
        if code != 0:
            send(f"展示生成失败:\n{output[-200:]}")
            sys.exit(1)

    # Step 5: 读取推文文案并回复
    tweet_file = RESULTS_DIR / "tweet.txt"
    if tweet_file.exists():
        tweet_text = tweet_file.read_text().strip()
    else:
        tweet_text = "(推文文案未生成)"

    # 汇总结果
    gifs = list(RESULTS_DIR.glob("*.gif"))
    compares = list(RESULTS_DIR.glob("compare_*"))

    # 分两条发送避免消息过长
    send(f"处理完成！结果汇总:\n- 对比图: {len(compares)}张\n- GIF展示: {len(gifs)}个\n- 推文文案已生成\n文件位置: ~/campaign_images/results/")
    time.sleep(2)
    # 推文文案截取前300字符
    tweet_preview = tweet_text[:300] + ("..." if len(tweet_text) > 300 else "")
    send(f"推文文案:\n{tweet_preview}")

    print("\n" + "=" * 60)
    print("Demo 完成！")
    print(f"  对比图: {len(compares)} 张")
    print(f"  GIF: {len(gifs)} 个")
    print(f"  推文: {tweet_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
