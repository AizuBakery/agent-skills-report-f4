#!/usr/bin/env python3
"""Batch process pending images: two-stage cleanup+style editing with comparison."""

import base64, io, os, sys
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image, ImageOps

MODEL_NAME = "inclusionai/ming-flash-omni-2.0"
PENDING_DIR = Path.home() / "campaign_images" / "images" / "new"
CANDIDATES_DIR = Path.home() / "campaign_images" / "candidates"
RESULTS_DIR = Path.home() / "campaign_images" / "results"


def get_client():
    key = os.getenv("ZENMUX_API_KEY")
    if not key:
        print("Error: ZENMUX_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return genai.Client(
        api_key=key, vertexai=True,
        http_options=types.HttpOptions(api_version='v1', base_url='https://zenmux.ai/api/vertex-ai')
    )

# original one, may bypass

MAX_DIM = 2048
MAX_BYTES = 2 * 1024 * 1024  # 2MB

def compress_image(image_data: bytes) -> tuple[bytes, str]:
    """Resize and compress image to fit API limits. Returns (data, mime_suffix)."""
    img = Image.open(io.BytesIO(image_data))
    img = ImageOps.exif_transpose(img)
    if img.mode == "RGBA":
        img = img.convert("RGB")

    # Resize if too large
    w, h = img.size
    if max(w, h) > MAX_DIM:
        ratio = MAX_DIM / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # Compress to JPEG
    buf = io.BytesIO()
    quality = 85
    img.save(buf, format="JPEG", quality=quality)
    while buf.tell() > MAX_BYTES and quality > 30:
        buf = io.BytesIO()
        quality -= 15
        img.save(buf, format="JPEG", quality=quality)

    return buf.getvalue(), "jpeg"


def analyze_cleanup(client, image_data):
    """Stage 1 Director: identify distractions and generate cleanup instruction."""
    compressed, mime_suffix = compress_image(image_data)
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=compressed, mime_type=f"image/{mime_suffix}"),
            (
                "You are an expert photo retoucher. Your job is to find EVERY non-natural element "
                "that does not belong in an ideal, clean photograph of the main subject.\n"
                "Scan the ENTIRE image carefully — foreground, midground, background, edges, corners.\n"
                "Look for:\n"
                "- People, pedestrians, crowds, tourists\n"
                "- Vehicles: cars, trucks, buses, motorcycles, trailers\n"
                "- Street furniture: metal barriers, railings, fences, bollards, trash cans\n"
                "- Traffic signs, traffic lights\n"
                "- Any object partially blocking or obscuring the main subject\n"
                "- Wires, cables, construction equipment, modern clutter\n"
                "DO NOT list: lanterns, decorations, cultural ornaments, inscriptions, signboards, "
                "mountains, trees, sky, natural scenery, architectural features.\n"
                "Be SPECIFIC: describe exact items and their locations "
                "(e.g. 'the silver car on the right', 'three pedestrians in the foreground'), "
                "not generic categories.\n"
                "If distractions exist, write ONE cleanup instruction:\n"
                "'Repaint [specific items with locations] with clean ground/pavement/empty space, "
                "keep [main subject] exactly as it is.'\n"
                "If truly nothing to clean, return: NONE\n"
                "Return ONLY the instruction or NONE."
            )
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT"])
    )
    for part in resp.parts:
        if part.text and part.text.strip():
            return part.text.strip()
    return "NONE"


def analyze_3styles(client, image_data):
    """Stage 2 Director: generate 3 style instructions for a cleaned-up image."""
    compressed, mime_suffix = compress_image(image_data)
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=compressed, mime_type=f"image/{mime_suffix}"),
            (
                "You are an expert AI art director. This image has already been cleaned up. "
                "Suggest exactly 3 DIFFERENT style editing instructions, numbered 1. 2. 3.:\n"
                "- Line 1: Atmosphere — spring with cherry blossoms, summer with lush green, autumn with warm golden leaves, or winter with frost and snow\n"
                "- Line 2: Dramatic — golden hour, sunset glow, rain scene, snow scene, starry night, or moonlit night\n"
                "- Line 3: Artistic — watercolor, oil painting, ink wash, ukiyo-e, impressionist, or pencil sketch\n"
                "Keep the result realistic and natural-looking.\n"
                "MUST KEEP the main subject intact.\n"
                "If the image contains text, inscriptions, or calligraphy, do NOT repaint those areas — "
                "focus style changes on lighting, sky, and atmosphere only.\n"
                "NEVER add any new text, watermarks, or labels unless the exact text is specified in quotes.\n"
                "NEVER say 'remove' or 'delete'. Return ONLY the 3 numbered lines, nothing else."
            )
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT"])
    )
    instructions = []
    for part in resp.parts:
        if part.text:
            for line in part.text.strip().split("\n"):
                line = line.strip()
                if line and line[0].isdigit():
                    clean = line.lstrip("0123456789.").strip()
                    if clean:
                        instructions.append(clean)
    while len(instructions) < 3:
        instructions.append("Enhance the lighting and atmosphere dramatically")
    return instructions[:3]


def edit_image(client, image_data, instruction, is_cleanup=False):
    """Creator: generate edited image from raw bytes."""
    compressed, mime_suffix = compress_image(image_data)
    if is_cleanup:
        prompt = (
            f"Erase and inpaint the following items: {instruction}. "
            "Fill erased areas with natural background that seamlessly matches the surroundings. "
            "Do NOT add any new objects, people, or figures. "
            "Every listed item must be completely removed."
        )
    else:
        prompt = f"Edit this image: {instruction}. Do NOT add any new objects, people, or figures that are not in the original."
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=compressed, mime_type=f"image/{mime_suffix}"),
            prompt
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"])
    )
    for part in resp.parts:
        if part.file_data and part.file_data.file_uri and part.file_data.file_uri.startswith("data:"):
            _, encoded = part.file_data.file_uri.split(",", 1)
            return Image.open(io.BytesIO(base64.b64decode(encoded)))
        if part.inline_data is not None:
            return Image.open(io.BytesIO(part.inline_data.data))
    return None


def img_to_bytes(img: Image.Image) -> bytes:
    """Convert PIL Image to JPEG bytes."""
    buf = io.BytesIO()
    if img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def score_image(client, orig_data, edit_data, instruction):
    """Critic: score an edited image 0-100."""
    orig_compressed, orig_suffix = compress_image(orig_data)
    edit_compressed, edit_suffix = compress_image(edit_data)
    resp = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            types.Part.from_bytes(data=orig_compressed, mime_type=f"image/{orig_suffix}"),
            types.Part.from_bytes(data=edit_compressed, mime_type=f"image/{edit_suffix}"),
            (
                "Compare the original (first image) with the edited version (second image). "
                "Score the edit 0-100 based on:\n"
                "1. Structure preservation (30 points): Does the main subject look the same? "
                "Same shape, proportions, position? No distortion or warping?\n"
                "2. Cleanup quality (25 points): Were distracting elements (vehicles, people, barriers) "
                "successfully replaced with natural-looking background?\n"
                "3. No hallucinations (25 points): Are there any NEW objects, people, or figures "
                "that did NOT exist in the original? If yes, score 0 for this category.\n"
                "4. Visual quality (20 points): No artifacts, no blurry patches, no unnatural edges, "
                "colors look natural and consistent?\n"
                "Return ONLY the integer score."
            )
        ],
        config=types.GenerateContentConfig(response_modalities=["TEXT"])
    )
    for part in resp.parts:
        if part.text:
            digits = ''.join(c for c in part.text if c.isdigit())[:3]
            if digits:
                return int(digits)
    return 50


def make_comparison(original_img: Image.Image, edited_imgs: list) -> Image.Image:
    """Stitch original + N edited images side by side."""
    all_imgs = [original_img] + edited_imgs
    h = max(img.height for img in all_imgs)

    resized = []
    for img in all_imgs:
        w = int(img.width * h / img.height)
        resized.append(img.resize((w, h), Image.LANCZOS))

    divider_w = 4
    total_w = sum(r.width for r in resized) + divider_w * (len(resized) - 1)
    canvas = Image.new("RGB", (total_w, h), (255, 255, 255))

    x = 0
    for i, r in enumerate(resized):
        canvas.paste(r.convert("RGB"), (x, 0))
        x += r.width + divider_w

    return canvas


NUM_CLEANUP_CANDIDATES = 3


def main():
    CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    client = get_client()

    images = sorted([p for p in PENDING_DIR.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    total = len(images)
    print(f"Found {total} images to process\n", flush=True)

    for idx, img_path in enumerate(images, 1):
        print(f"[{idx}/{total}] {img_path.name}", flush=True)

        with open(img_path, "rb") as f:
            data = f.read()

        # Stage 1: Cleanup — isolate main subject
        try:
            cleanup_inst = analyze_cleanup(client, data)
            print(f"  🧹 Cleanup: {cleanup_inst[:80]}...", flush=True)
        except Exception as e:
            print(f"  ✗ Cleanup director failed: {e}", file=sys.stderr, flush=True)
            continue

        skip_cleanup = cleanup_inst.upper() == "NONE" or "no cleanup" in cleanup_inst.lower()
        if skip_cleanup:
            print(f"  ⏭ Scene already clean, skipping cleanup edit", flush=True)
            cleaned = ImageOps.exif_transpose(Image.open(img_path))
        else:
            # Generate multiple cleanup candidates, pick the best
            cleanup_candidates = []
            for ci in range(NUM_CLEANUP_CANDIDATES):
                try:
                    result = edit_image(client, data, cleanup_inst, is_cleanup=True)
                    if result is not None:
                        cleanup_candidates.append(result)
                        # Save each candidate for review
                        cand_path = CANDIDATES_DIR / f"cleanup_{img_path.stem}_c{ci+1}.png"
                        result.save(str(cand_path))
                        print(f"  🔄 Cleanup candidate {ci+1}/{NUM_CLEANUP_CANDIDATES} saved: {cand_path}", flush=True)
                except Exception as e:
                    print(f"  ✗ Cleanup candidate {ci+1} failed: {e}", file=sys.stderr, flush=True)

            if not cleanup_candidates:
                print(f"  ✗ All cleanup candidates failed, using original", flush=True)
                cleaned = ImageOps.exif_transpose(Image.open(img_path))
            elif len(cleanup_candidates) == 1:
                cleaned = cleanup_candidates[0]
                print(f"  ✓ Using single cleanup candidate", flush=True)
            else:
                # Score and pick best cleanup
                best_score, best_idx = -1, 0
                for ci, cand in enumerate(cleanup_candidates):
                    try:
                        cand_data = img_to_bytes(cand)
                        sc = score_image(client, data, cand_data, cleanup_inst)
                        print(f"  📊 Cleanup candidate {ci+1} score: {sc}", flush=True)
                        if sc > best_score:
                            best_score, best_idx = sc, ci
                    except Exception as e:
                        print(f"  ✗ Scoring candidate {ci+1} failed: {e}", file=sys.stderr, flush=True)
                cleaned = cleanup_candidates[best_idx]
                print(f"  ✓ Best cleanup: candidate {best_idx+1} (score {best_score})", flush=True)

            clean_path = CANDIDATES_DIR / f"cleaned_{img_path.stem}.png"
            cleaned.save(str(clean_path))
            print(f"  💾 Cleaned: {clean_path}", flush=True)

        # Stage 2: Style variations on cleaned image
        cleaned_data = img_to_bytes(cleaned)
        try:
            instructions = analyze_3styles(client, cleaned_data)
            for i, inst in enumerate(instructions):
                print(f"  🎨 Style {i+1}: {inst[:80]}...", flush=True)
        except Exception as e:
            print(f"  ✗ Style director failed: {e}", file=sys.stderr, flush=True)
            continue

        styled_imgs = []
        for i, inst in enumerate(instructions):
            try:
                styled = edit_image(client, cleaned_data, inst)
                if styled is None:
                    print(f"  ✗ Style {i+1} no image returned", file=sys.stderr, flush=True)
                    continue
                style_path = CANDIDATES_DIR / f"styled_{img_path.stem}_v{i+1}.png"
                styled.save(str(style_path))
                styled_imgs.append(styled)
                print(f"  💾 Style {i+1} saved: {style_path}", flush=True)
            except Exception as e:
                print(f"  ✗ Style {i+1} failed: {e}", file=sys.stderr, flush=True)

        # Save pairwise comparisons: Original | Edited for each style
        original = ImageOps.exif_transpose(Image.open(img_path))

        for i, styled in enumerate(styled_imgs):
            comp = make_comparison(original, [styled])
            out_path = RESULTS_DIR / f"compare_{img_path.stem}_v{i+1}.jpg"
            comp.save(str(out_path), quality=92)
            print(f"  ✓ Comparison saved: {out_path}", flush=True)

        print(flush=True)

    print(f"\nDone! Edited images in {CANDIDATES_DIR}, comparisons in {RESULTS_DIR}", flush=True)


if __name__ == "__main__":
    main()
