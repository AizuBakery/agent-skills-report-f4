# From Agent to Skills: A Paradigm Shift in AI Agent Architecture

> 技术报告：从 Agent 到 Skills — AI 智能体架构的范式转变

This repository contains the companion code and technical report for understanding the paradigm shift from monolithic AI Agents to composable Skills + MCP + A2A architecture.

## What's Inside

### Technical Report

- [`技术报告_从Agent到Skills的范式转变.md`](技术报告_从Agent到Skills的范式转变.md) — Full technical report (Chinese), covering:
  - Why Skills replace monolithic Agents
  - Core concepts: Agent, Skills, MCP, OpenClaw, A2A
  - Real-world project walkthrough
  - Experiment: Claude Code vs OpenClaw side-by-side comparison

### Skills (Working Code)

```
skills/
├── auto-twitter-campaign/     ← Core project: AI image processing + tweet generation
│   ├── SKILL.md               ← Skill metadata + instructions (3-layer progressive disclosure)
│   └── scripts/
│       ├── campaign.py        ← Orchestrator (thin layer)
│       └── batch_compare.py   ← Image pipeline (Director-Creator-Critic pattern)
│
├── wechat/                    ← WeChat keyboard automation skill
│   ├── skill.json + prompt.md
│   └── scripts/               ← Shell wrappers for send/read
│
└── wechat-bridge/             ← WeChat ↔ OpenClaw bridge
    ├── skill.json + prompt.md
    └── scripts/
        ├── demo_case1.py      ← Claude Code approach (deterministic script)
        ├── bridge_openclaw.py ← OpenClaw approach (thin IO adapter + Agent reasoning)
        └── bridge.py          ← Original version (superseded)
```

## Key Architecture

```
┌─────────────────────────────────────────────────────┐
│                  2026 Agentic AI Stack               │
│                                                     │
│  Application:  OpenClaw / Claude Code / Cursor       │
│  Knowledge:    Skills (teach HOW to do things)       │
│  Reasoning:    Agent (decide WHAT to do)             │
│  Tools:        MCP (connect to external services)    │
│  Collaboration: A2A (Agent-to-Agent delegation)      │
│  Foundation:   LLM API / Local models                │
└─────────────────────────────────────────────────────┘
```

## Requirements

- Python 3.10+
- `google-genai` SDK
- `Pillow` for image processing
- `ZENMUX_API_KEY` environment variable (for Ming-flash-omni-2.0 API)
- OpenClaw (optional, for Agent-based execution)

## License

MIT
