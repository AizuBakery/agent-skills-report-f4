# WeChat OpenClaw 技能

<thinking>
现在我需要创建一个README文件来总结整个技能，并提供快速开始指南。
</thinking>

通过WeChat MCP服务器实现微信消息自动化的OpenClaw技能。

## 功能特性

✅ 发送微信消息给指定联系人
✅ 读取与联系人的聊天历史记录
✅ 列出所有微信联系人
✅ 支持通过昵称或微信ID识别联系人

## 快速开始

### 1. 安装依赖

```bash
# 安装uv（Python包管理器）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 下载wechat-mcp服务器
mkdir -p ~/wechat-integration
cd ~/wechat-integration
git clone https://github.com/JettChenT/wechat-mcp.git
```

### 2. 配置OpenClaw

编辑 `~/.openclaw/openclaw.json`，添加：

```json
{
  "mcpServers": {
    "wechat": {
      "command": "uv",
      "args": [
        "--directory",
        "~/wechat-integration/wechat-mcp",
        "run",
        "-m",
        "src.mcp"
      ]
    }
  }
}
```

### 3. 安装技能

```bash
# 复制技能到OpenClaw
cp -r ~/projects/wechat-openclaw-skill ~/.openclaw/skills/wechat

# 验证安装
openclaw skills
```

### 4. 使用示例

```bash
# 发送消息
./scripts/send_message.sh "张三" "你好，这是测试消息"

# 读取聊天记录
./scripts/read_chat.sh "李四" 20

# 列出联系人
./scripts/list_contacts.sh
```

## 重要提示

⚠️ **风险警告**：
- 微信对自动化有严格限制，频繁使用可能导致账号被封
- 仅建议用于个人测试和学习目的
- 请遵守微信服务条款

## 系统要求

- macOS系统
- WeChat for Mac 3.x
- 修改版微信（用于导出聊天记录）
- Python 3.8+（通过uv管理）

## 文件说明

- `skill.json` - 技能配置文件
- `prompt.md` - 技能使用说明和触发条件
- `setup.md` - 详细的安装和配置指南
- `scripts/` - 便捷脚本工具
  - `send_message.sh` - 发送消息脚本
  - `read_chat.sh` - 读取聊天记录脚本
  - `list_contacts.sh` - 列出联系人脚本

## 故障排除

详见 `setup.md` 中的故障排除章节。

## 技术架构

```
OpenClaw
    ↓
WeChat Skill (此技能)
    ↓
WeChat MCP Server (JettChenT/wechat-mcp)
    ↓
WeChat for Mac (修改版)
```

## 参考资源

- [wechat-mcp GitHub](https://github.com/JettChenT/wechat-mcp)
- [wechat-exporter](https://github.com/JettChenT/wechat-exporter)
- [OpenClaw文档](https://docs.openclaw.ai)

## 许可证

MIT License

## 作者

dandan - 2026-02-16
