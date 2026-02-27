# WeChat 消息技能 (v3 - 键盘模拟 + 截图OCR)

## 功能说明

通过键盘模拟和截图OCR实现以下功能：

1. **发送微信消息** - 使用聊天名称给好友发送文本消息
2. **读取聊天记录** - 截图当前聊天窗口并OCR提取文字

## 使用方法

### 发送消息

```bash
~/wechat-integration/wechat send <聊天名称> <消息内容>
# 示例: ~/wechat-integration/wechat send 张三 "你好"
```

### 读取聊天记录

```bash
~/wechat-integration/wechat chat <聊天名称>
# 示例: ~/wechat-integration/wechat chat 张三
```

OCR结果中，`左` 表示对方消息，`右` 表示自己消息，`中` 通常是时间戳。

## 技术说明

- 使用 AppleScript 键盘模拟控制微信（Cmd+F搜索、剪贴板粘贴、回车发送）
- 使用 macOS Vision 框架对截图做 OCR 提取聊天文字
- WeChat 4.x 不暴露 AX 树，因此不使用 Accessibility API 读取UI元素
- iTerm2（或终端）需要在系统设置中获得辅助功能权限
