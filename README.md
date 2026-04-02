# From Agent to Skills: A Paradigm Shift in AI Agent Architecture

### Skills (Working Code)

```
skills/
├── auto-twitter-campaign/     ← Core project: AI image processing + tweet generation
│   ├── SKILL.md               ← Skill metadata + instructions (3-layer progressive process)
│   └── scripts/
│       ├── campaign.py        ← Orchestrator
│       └── batch_compare.py   ← Image pipeline ()
│
├──
...
~/openclaw/skills/                      
├── filesystem/                           ← 教 Agent 怎么用 Filesystem MCP
│   ├── skill.json
│   └── prompt.md
└── xhs/                               ← 教 Agent 怎么联小红书

```


## Requirements

- Python 3.10+
- `google-genai` SDK
- `Pillow` for image processing
- `ZENMUX_API_KEY` environment variable (for Ming-flash-omni-2.0 API)
- OpenClaw (optional, for Agent-based execution)

## License

MIT


## Credit

Forge450, for internal demo usage in Japan
