#!/bin/bash
# 启动微信消息桥接器
# 用法: ./start.sh <聊天名称> [轮询间隔秒数]
# 示例: ./start.sh "文件传输助手" 30
CHAT="${1:?用法: ./start.sh <聊天名称> [间隔秒数]}"
INTERVAL="${2:-30}"
python3 ~/.openclaw/skills/wechat-bridge/scripts/bridge.py --chat "$CHAT" --interval "$INTERVAL"
