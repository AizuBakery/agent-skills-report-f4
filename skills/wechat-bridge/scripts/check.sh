#!/bin/bash
# 单次检查微信消息
# 用法: ./check.sh <聊天名称>
CHAT="${1:?用法: ./check.sh <聊天名称>}"
python3 ~/.openclaw/skills/wechat-bridge/scripts/bridge.py --chat "$CHAT" --once
