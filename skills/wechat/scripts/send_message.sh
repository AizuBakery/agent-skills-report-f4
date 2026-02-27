#!/bin/bash

# WeChat消息发送脚本 (键盘模拟版本)
# 用法: ./send_message.sh <聊天名称> <消息内容>

CHAT_NAME="$1"
MESSAGE="$2"

if [ -z "$CHAT_NAME" ] || [ -z "$MESSAGE" ]; then
    echo "用法: $0 <聊天名称> <消息内容>"
    echo "示例: $0 张三 '你好，这是测试消息'"
    exit 1
fi

~/wechat-integration/wechat send "$CHAT_NAME" "$MESSAGE"
