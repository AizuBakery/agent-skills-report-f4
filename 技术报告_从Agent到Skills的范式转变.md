# 技术报告：从 Agent 到 Skills — AI 智能体架构的范式转变

> **关键词**：Agent Skills, MCP, OpenClaw, A2A, Agentic AI, 模块化架构

---

## 一、谁提出了从 Agent 到 Skills 的转变？

### 1.1 起源：Anthropic 的两步棋

**Anthropic** 在不到 14 个月内连续发布了两个开放标准：

| 时间 | 事件 | 意义 |
|:---|:---|:---|
| **2024年11月** | Anthropic 开源 **MCP（Model Context Protocol）** | 解决 AI 模型与外部工具/数据的连接问题 |
| **2025年10月** | Anthropic 在 Claude Code 中推出 **Agent Skills** | 解决 AI 模型的领域专业知识加载问题 |
| **2025年12月18日** | Anthropic 将 Agent Skills 作为**开放标准**发布 | 48小时内被 Microsoft、OpenAI 采纳 |
| **2025年12月** | MCP 捐赠给 **Linux 基金会**（Agentic AI Foundation） | 从公司项目升级为行业标准 |

Anthropic 工程博客原文：

> "Building a skill for an agent is like putting together an onboarding guide for a new hire. Instead of building fragmented, custom-designed agents for each use case, anyone can now specialize their agents with composable capabilities."

### 1.2 行业响应

Agent Skills 开放标准发布后，各家跟进很快：

- **Microsoft**：48小时内宣布支持
- **OpenAI Codex**：迅速集成 Skills 格式
- **Cursor、Codebuddy**：原生支持
- **OpenClaw**：成为 Skills 生态最大的消费者之一，拥有 3000+ 社区 Skills
- **Spring AI**：2026年1月发布 Agent Skills 集成模式

Gartner 2024年的预测已经应验：到2026年，75% 的 AI 项目聚焦于可组合的 Skills 而非单体 Agent。


---

## 参考资料

### 官方资源
- [Anthropic: Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- [Anthropic: Introducing Agent Skills](https://www.anthropic.com/news/skills)
- [Model Context Protocol Specification (2025-03-26)](https://modelcontextprotocol.io/specification/2025-03-26)

### 技术分析
- [Claude Skills: A Technical Deep Dive into Agentic Orchestration](https://avasdream.com/blog/claude-skills-technical-guide)
- [Agent Skills vs MCP - How do you choose?](https://ravichaganti.com/blog/agent-skills-vs-model-context-protocol-how-do-you-choose/)
- [Skills vs MCP: Understanding Two Layers of the Same Stack](https://www.getmaxim.ai/blog/the-skills-vs-mcp-debate-understanding-two-layers-of-the-same-stack/)
- [Claude Skills vs MCP - What's the Difference](https://blog.dante.company/en/articles/claude-skills-vs-mcp-comparison)
- [Stop Building Agents, Start Building Skills](https://www.brgr.one/blog/stop-building-agents-build-skills)

### OpenClaw
- [OpenClaw Architecture, Explained](https://ppaolo.substack.com/p/openclaw-system-architecture-overview)
- [OpenClaw: A Deep Dive into the Architecture](https://rajvijayaraj.substack.com/p/openclaw-architecture-a-deep-dive)
- [OpenClaw: 180K GitHub Stars and Agentic AI's Security Wake-Up Call](https://learndevrel.com/blog/openclaw-ai-agent-phenomenon)
- [OpenClaw Security Analysis](https://agenteer.com/blog/security-analysis-of-openclaw-and-the-ai-agent-era)

### 行业趋势
- [The Rise of Skills: Why 2026 Is the Year of Specialized AI Agents](https://midokura.com/the-rise-of-skills-why-2026-is-the-year-of-specialized-ai-agents/)
- [The Hard Truth About Agent Skills](https://www.teamday.ai/blog/agent-skills-hard-truth)
- [MCP vs A2A: The Complete Guide to AI Agent Protocols in 2026](https://learndevrel.com/blog/mcp-vs-a2a)
- [The Agent Protocol Stack: MCP + A2A + A2UI](https://subhadipmitra.com/blog/2026/agent-protocol-stack/)
- [A Year of MCP: From Internal Experiment to Industry Standard](https://www.pento.ai/blog/a-year-of-mcp-2025-review)

### 学术论文
- [Agentic AI: Architecture, Acquisition, Security, and the Path Forward (arXiv:2602.12430)](https://arxiv.org/html/2602.12430v1)
- [A Survey of the Model Context Protocol (MCP)](https://www.preprints.org/manuscript/202504.0245/v1)
