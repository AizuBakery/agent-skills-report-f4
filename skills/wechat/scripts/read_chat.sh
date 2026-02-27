#!/bin/bash

# WeChat聊天记录读取脚本 (截图OCR版本)
# 用法: ./read_chat.sh <聊天名称>

CHAT_NAME="$1"

if [ -z "$CHAT_NAME" ]; then
    echo "用法: $0 <聊天名称>"
    echo "示例: $0 张三"
    exit 1
fi

~/wechat-integration/wechat chat "$CHAT_NAME"
