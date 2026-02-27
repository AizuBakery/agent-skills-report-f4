#!/usr/bin/env python3
"""
Auto Twitter Campaign — image editing pipeline + AI tweet content generator.
Uses Ming-flash-omni-2.0 (Zenmux) for vision/editing and tweet text generation.
"""

import argparse
import glob
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow not found. Install: pip install Pillow", file=sys.stderr)
    sys.exit(1)

RESULTS_DIR = Path.home() / "campaign_images" / "results"
SCRIPT_DIR = Path(__file__).resolve().parent


# ── GIF Generation ──────────────────────────────────────────

def find_compare_images(results_dir):
    """Find compare images grouped by base image name."""
    files = sorted(glob.glob(str(results_dir / "compare_*.jpg")))
    files += sorted(glob.glob(str(results_dir / "compare_*.png")))

    groups = defaultdict(list)
    for f in files:
        base = os.path.basename(f)
        match = re.match(r"(compare_.+?)(_v\d+)?\.(jpg|png)$", base)
        if match:
            groups[match.group(1)].append(f)

    return dict(groups)


def make_gif(image_paths, out_path, hold_sec=2.5, max_long_side=1200):
    """Create a GIF cycling through comparison images."""
    raw = []
    for p in image_paths:
        img = Image.open(p).convert("RGB")
        ratio = min(max_long_side / max(img.width, img.height), 1.0)
        if ratio < 1.0:
            img = img.resize(
                (int(img.width * ratio), int(img.height * ratio)),
                Image.LANCZOS,
            )
        raw.append(img)

    canvas_w = max(img.width for img in raw)
    canvas_h = max(img.height for img in raw)

    frames = []
    for img in raw:
        if img.size == (canvas_w, canvas_h):
            frame = img
        else:
            frame = Image.new("RGB", (canvas_w, canvas_h), (30, 30, 30))
            x = (canvas_w - img.width) // 2
            y = (canvas_h - img.height) // 2
            frame.paste(img, (x, y))
        frames.append(frame.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                                     dither=Image.Dither.FLOYDSTEINBERG))

    frames[0].save(
        str(out_path), save_all=True, append_images=frames[1:],
        duration=int(hold_sec * 1000), loop=0,
    )
    print(f"  GIF saved: {out_path} ({len(frames)} frames, {canvas_w}x{canvas_h})")


def generate_gifs(results_dir):
    """Generate per-group and all-in-one showcase GIFs."""
    groups = find_compare_images(results_dir)
    if not groups:
        print("No compare images found, skipping GIF generation.")
        return

    print(f"Found {sum(len(v) for v in groups.values())} compare images "
          f"in {len(groups)} groups\n")

    for base_name, paths in sorted(groups.items()):
        if len(paths) > 1:
            gif_path = results_dir / f"{base_name}.gif"
            print(f"Creating GIF for {base_name} ({len(paths)} versions)...")
            make_gif(paths, gif_path)

    all_images = []
    for _, paths in sorted(groups.items()):
        all_images.extend(paths)

    if len(all_images) > 1:
        showcase_path = results_dir / "showcase_all.gif"
        print(f"\nCreating showcase GIF ({len(all_images)} images total)...")
        make_gif(all_images, showcase_path, hold_sec=2.5)


# ── AI Tweet Text Generation ───────────────────────────────

def get_client():
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("Error: google-genai not found. Install: pip install google-genai", file=sys.stderr)
        sys.exit(1)

    key = os.getenv("ZENMUX_API_KEY")
    if not key:
        print("Error: ZENMUX_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return genai.Client(
        api_key=key, vertexai=True,
        http_options=types.HttpOptions(api_version='v1', base_url='https://zenmux.ai/api/vertex-ai')
    )


def generate_tweet_text(results_dir, description=None, compare_files=None):
    """Use AI to generate tweet text from description and comparison images.
    If compare_files is provided, only use those for context instead of all results."""
    from google.genai import types
    import io

    MODEL_NAME = "inclusionai/ming-flash-omni-2.0"

    # Read description
    desc_path = results_dir / "description.txt"
    if description:
        desc = description
        with open(desc_path, "w", encoding="utf-8") as f:
            f.write(desc)
    elif desc_path.exists():
        with open(desc_path, "r", encoding="utf-8") as f:
            desc = f.read().strip()
    else:
        desc = None

    # Pick comparison images for visual context
    if compare_files is None:
        compare_files = sorted(glob.glob(str(results_dir / "compare_*.jpg")))
        compare_files += sorted(glob.glob(str(results_dir / "compare_*.png")))
    else:
        compare_files = [str(f) for f in compare_files]

    client = get_client()
    contents = []

    # Add a comparison image for visual context (first one)
    if compare_files:
        img = Image.open(compare_files[0]).convert("RGB")
        ratio = min(1200 / max(img.width, img.height), 1.0)
        if ratio < 1.0:
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        contents.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))

    # Count scenes and styles
    groups = find_compare_images(results_dir)
    num_scenes = len(groups)
    num_images = sum(len(v) for v in groups.values())

    prompt = (
        "You are a social media content writer. Write a Twitter/X post for an AI image editing showcase.\n\n"
    )

    if desc:
        prompt += f"Scene description (from the photographer): {desc}\n\n"
    else:
        prompt += "Analyze the comparison image to understand the scene and location.\n\n"

    prompt += (
        f"This showcase has {num_scenes} scene(s) with {num_images} comparison image(s).\n"
        "The image shows: Left = original raw photo, Right = AI-edited version.\n"
        "The AI model used is Ming-flash-omni-2.0.\n\n"
        "Follow this exact format (each line starts with an emoji, NO markdown, NO bold, NO headers):\n\n"
        "📍 [Location name in English (中文)] — [brief cultural context]\n"
        "📅 [Occasion or season if relevant]\n"
        "🏔️ Scenes: [list the specific landmarks/views, use both English and Chinese names]\n"
        "🤖 Agent Task: [what the AI did, e.g. stylize travel photos, remove tourists, enhance atmosphere]\n"
        "⚙️ Engine: Ming-flash-omni-2.0\n"
        "\n"
        "[1-3 sentences: cultural story, legend, or blessing related to the place. Be vivid and heartfelt.]\n"
        "\n"
        "[1 sentence: technical note about what the model handled well, e.g. textures, inpainting, sky replacement]\n"
        "(Left: Raw photo → Right: Omni magic ✨)\n"
        "\n"
        "[5-8 relevant hashtags, always include #MingOmni and #OpenClaw]\n\n"
        "Keep Chinese place names in parentheses after English. "
        "No markdown formatting. No numbered lists. No section titles. "
        "Output ONLY the post text, nothing else."
    )
    contents.append(prompt)

    response = client.models.generate_content(
        model=MODEL_NAME, contents=contents,
        config=types.GenerateContentConfig(response_modalities=["TEXT"])
    )

    tweet = None
    for part in response.parts:
        if part.text and part.text.strip():
            tweet = part.text.strip()
            # Strip surrounding quotes if present
            if (tweet.startswith('"') and tweet.endswith('"')) or \
               (tweet.startswith("'") and tweet.endswith("'")):
                tweet = tweet[1:-1].strip()
            break

    if not tweet:
        tweet = (
            "🤖 AI image editing showcase — Ming-flash-omni-2.0\n"
            "(Left: Original → Right: AI ✨)\n"
            "#MingOmni #AIPhotography #OpenClaw"
        )

    tweet_path = results_dir / "tweet.txt"
    with open(tweet_path, "w", encoding="utf-8") as f:
        f.write(tweet)

    print(f"\nTweet saved: {tweet_path}")
    print(f"\n{'='*50}")
    print(tweet)
    print(f"{'='*50}")
    print(f"Characters: {len(tweet)}")

    return tweet


# ── Commands ────────────────────────────────────────────────

def cmd_process(args):
    """Run batch image processing (cleanup + style editing). Returns list of new compare files."""
    import importlib.util

    # Record modification times of existing results before processing
    before = {p: p.stat().st_mtime for p in RESULTS_DIR.glob("compare_*")}

    if hasattr(args, 'image') and args.image:
        # Single image mode: temporarily override PENDING_DIR content
        image_path = Path(args.image).resolve()
        if not image_path.exists():
            print(f"Error: image not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        # Symlink into a temp dir so batch_compare picks it up
        import tempfile, shutil
        tmp_dir = Path(tempfile.mkdtemp(prefix="campaign_single_"))
        tmp_link = tmp_dir / image_path.name
        shutil.copy2(str(image_path), str(tmp_link))

        spec = importlib.util.spec_from_file_location("batch_compare", SCRIPT_DIR / "batch_compare.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        # Override PENDING_DIR for single image
        orig_pending = mod.PENDING_DIR
        mod.PENDING_DIR = tmp_dir
        mod.main()
        mod.PENDING_DIR = orig_pending
        shutil.rmtree(tmp_dir, ignore_errors=True)
    else:
        spec = importlib.util.spec_from_file_location("batch_compare", SCRIPT_DIR / "batch_compare.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main()

    # Find newly created or updated compare files
    new_files = []
    for p in sorted(RESULTS_DIR.glob("compare_*")):
        if p not in before or p.stat().st_mtime > before[p]:
            new_files.append(p)
    return new_files


def cmd_showcase(args, compare_files=None):
    """Generate GIFs and tweet text from existing results."""
    results_dir = Path(args.results_dir) if args.results_dir else RESULTS_DIR

    if not results_dir.is_dir():
        print(f"Error: results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    print("Generating GIFs...")
    generate_gifs(results_dir)

    print("\nGenerating tweet text (AI)...")
    generate_tweet_text(results_dir, description=args.description, compare_files=compare_files)

    print("\nDone!")


def cmd_run(args):
    """Full pipeline: process → showcase."""
    print("=" * 50)
    print("Stage 1: Processing pending images")
    print("=" * 50)
    new_files = cmd_process(args)
    print(f"\nNew compare files: {len(new_files)}")

    print("\n" + "=" * 50)
    print("Stage 2: Generating showcase + tweet text")
    print("=" * 50)
    args.results_dir = None
    cmd_showcase(args, compare_files=new_files if new_files else None)


def main():
    p = argparse.ArgumentParser(description="Auto Twitter Campaign — Content Generator")
    sub = p.add_subparsers(dest="cmd")

    proc_p = sub.add_parser("process", help="Batch process pending images")
    proc_p.add_argument("--image", help="Process a specific image")

    show_p = sub.add_parser("showcase", help="Generate GIFs + tweet text from results")
    show_p.add_argument("--results-dir", help="Results directory (default: ~/campaign_images/results)")
    show_p.add_argument("--description", help="Scene description for tweet generation")

    run_p = sub.add_parser("run", help="Full pipeline: process → showcase")
    run_p.add_argument("--image", help="Process a specific image")
    run_p.add_argument("--description", help="Scene description for tweet generation")

    args = p.parse_args()

    if args.cmd == "process":
        cmd_process(args)
    elif args.cmd == "showcase":
        cmd_showcase(args)
    elif args.cmd == "run":
        cmd_run(args)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
