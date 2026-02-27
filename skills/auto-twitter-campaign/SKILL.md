---
name: auto-twitter-campaign
description: Autonomous AI image campaign content generator. Processes pending photos via Ming-flash-omni-2.0 (cleanup + style editing), creates side-by-side comparison images and GIF showcases, then auto-generates tweet text using AI. Use for requests like "run campaign", "process pending images", "generate tweet content", or "create showcase from results".
---

# Auto Twitter Campaign — Content Generator

Autonomous closed-loop image editing and tweet content generation pipeline.
No auto-posting — outputs ready-to-use tweet text + media files.

## Quick Start

```bash
# Full pipeline: process pending images → comparisons → GIFs → tweet text
python3 {baseDir}/scripts/campaign.py run

# Process pending images only (cleanup + style editing → comparison images)
python3 {baseDir}/scripts/campaign.py process

# Generate showcase GIFs + tweet text from existing comparison images in results/
python3 {baseDir}/scripts/campaign.py showcase

# Process a specific image
python3 {baseDir}/scripts/campaign.py process --image /path/to/photo.jpg

# Provide a scene description for better tweet text (otherwise AI auto-describes)
python3 {baseDir}/scripts/campaign.py showcase --description "大年初一华山，下棋亭、西峰和南峰"
```

## Requirements

- `ZENMUX_API_KEY` environment variable set
- `google-genai` and `Pillow` Python packages

## Directories

- Pending images: `~/campaign_images/pending/`
- Candidates (intermediate edits): `~/campaign_images/candidates/`
- Results (comparisons, GIFs, tweet text): `~/campaign_images/results/`

## Pipeline

1. **Cleanup Director** — Vision scans for distractions (tourists, vehicles, clutter), generates cleanup instruction
2. **Cleanup Creator** — Generates multiple cleanup candidates, critic picks the best
3. **Style Director** — Generates 3 style instructions (atmosphere, dramatic, artistic)
4. **Style Creator** — Applies each style to the cleaned image, saves comparison images
5. **Showcase** — Creates per-scene and all-in-one GIF showcases from comparison images
6. **Tweet Writer** — AI analyzes comparison images + description, generates concise tweet text

## Output

After running, `~/campaign_images/results/` will contain:
- `compare_*.jpg` — Side-by-side comparison images (original | edited)
- `compare_*.gif` — Per-scene animated GIFs cycling through style variants
- `showcase_all.gif` — Combined showcase GIF of all comparisons
- `tweet.txt` — AI-generated tweet text ready to copy-paste
- `description.txt` — Scene description (user-provided or auto-generated)
