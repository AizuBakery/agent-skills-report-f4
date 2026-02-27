# WeChat OpenClaw 技能配置指南

## 前置要求

1. **macOS系统**
2. **WeChat for Mac 4.x** - 需要正在运行并已登录
3. **iTerm2 辅助功能权限** - 系统设置 → 隐私与安全 → 辅助功能 → 勾选 iTerm2
4. **BiboyQG/WeChat-MCP** - 已安装在 `~/wechat-integration/wechat-mcp-venv/`

## 安装步骤

### 1. 安装 WeChat-MCP

```bash
mkdir -p ~/wechat-integration && cd ~/wechat-integration
python3 -m venv wechat-mcp-venv
wechat-mcp-venv/bin/pip install wechat-mcp
```

### 2. 授予 iTerm2 辅助功能权限

系统设置 → 隐私与安全 → 辅助功能 → 添加并勾选 iTerm2

### 3. 验证

```bash
~/wechat-integration/wechat send 文件传输助手 "测试消息"
```

## 技术说明

- WeChat 4.x 不暴露 AX 树，无法使用 Accessibility API 读取 UI 元素
- 发送消息：AppleScript 键盘模拟（Cmd+F 搜索 → 粘贴联系人名 → 回车 → 粘贴消息 → 回车）
- 读取聊天：截图 + macOS Vision 框架 OCR

## 安全提示

- 频繁使用自动化工具可能导致微信账号被封禁
- 聊天记录包含敏感信息，请妥善保管
- 仅用于个人学习和测试
