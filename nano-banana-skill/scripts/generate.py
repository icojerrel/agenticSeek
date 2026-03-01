#!/usr/bin/env python3
"""
generate.py — nano-banana-skill main pipeline

Usage:
    python scripts/generate.py <prompt.json> --provider fal
    python scripts/generate.py <prompt.json> --provider gemini
"""

import argparse
import base64
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
STYLES_DIR = SKILL_ROOT / "styles"
OUTPUT_DIR = SKILL_ROOT / "output"


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def load_prompt(prompt_path: Path) -> dict:
    with open(prompt_path) as f:
        data = json.load(f)

    preset_name = data.get("meta", {}).get("style_preset")
    if preset_name:
        preset_path = STYLES_DIR / f"{preset_name}.json"
        if not preset_path.exists():
            print(f"[warn] style preset '{preset_name}' not found, skipping.")
        else:
            with open(preset_path) as f:
                preset = json.load(f)
            # Merge: preset values are defaults, explicit prompt values win
            data = _deep_merge(preset, data)

    return data


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def build_text_prompt(data: dict) -> str:
    p = data.get("product", {})
    s = data.get("shot", {})

    props_str = ""
    if s.get("props"):
        props_str = f" Props: {', '.join(s['props'])}."

    features_str = ""
    if p.get("key_features"):
        features_str = f" Features visible: {', '.join(p['key_features'])}."

    prompt = (
        f"Professional product photography of {p.get('name', 'a product')}, "
        f"a {p.get('category', '')}. "
        f"Color and material: {p.get('color', '')}, {p.get('material', '')}."
        f"{features_str} "
        f"Shot angle: {s.get('angle', 'front-facing')}. "
        f"Background: {s.get('background', 'white')}. "
        f"Lighting: {s.get('lighting', 'natural')}."
        f"{props_str} "
        f"Mood: {s.get('mood', 'clean')}. "
        f"Photorealistic, commercial quality, sharp focus."
    )
    return " ".join(prompt.split())


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def make_output_dir(campaign: str) -> Path:
    today = date.today().isoformat()
    out = OUTPUT_DIR / today / campaign
    out.mkdir(parents=True, exist_ok=True)
    return out


def save_prompt_snapshot(out_dir: Path, data: dict, ts: str) -> None:
    dest = out_dir / f"prompt_{ts}.json"
    with open(dest, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  [saved] prompt snapshot → {dest.relative_to(SKILL_ROOT)}")


def save_image(out_dir: Path, image_bytes: bytes, index: int, ts: str) -> None:
    dest = out_dir / f"image_{index}_{ts}.png"
    dest.write_bytes(image_bytes)
    print(f"  [saved] image {index} → {dest.relative_to(SKILL_ROOT)}")


# ---------------------------------------------------------------------------
# fal.ai provider
# ---------------------------------------------------------------------------

def generate_fal(prompt_text: str, data: dict, out_dir: Path, ts: str) -> None:
    try:
        import fal_client  # pip install fal-client
    except ImportError:
        sys.exit("[error] fal-client not installed. Run: pip install fal-client")

    api_key = os.environ.get("FAL_API_KEY")
    if not api_key:
        sys.exit("[error] FAL_API_KEY environment variable not set.")

    tech = data.get("technical", {})
    num_images = int(tech.get("num_images", 1))
    aspect_ratio = tech.get("aspect_ratio", "1:1")
    quality = tech.get("quality", "standard")

    model = "fal-ai/flux-pro" if quality == "hd" else "fal-ai/flux/dev"

    print(f"  [fal] model={model}, images={num_images}, ratio={aspect_ratio}")

    result = fal_client.run(
        model,
        arguments={
            "prompt": prompt_text,
            "num_images": num_images,
            "image_size": _fal_image_size(aspect_ratio),
            "num_inference_steps": 28 if quality == "hd" else 20,
        },
    )

    for i, img_obj in enumerate(result.get("images", []), start=1):
        # fal returns URLs; download them
        import urllib.request
        img_bytes, _ = urllib.request.urlretrieve(img_obj["url"])
        with open(img_bytes, "rb") as f:
            save_image(out_dir, f.read(), i, ts)


def _fal_image_size(aspect_ratio: str) -> str:
    mapping = {
        "1:1": "square_hd",
        "4:3": "landscape_4_3",
        "16:9": "landscape_16_9",
        "9:16": "portrait_16_9",
    }
    return mapping.get(aspect_ratio, "square_hd")


# ---------------------------------------------------------------------------
# Google Gemini Imagen provider
# ---------------------------------------------------------------------------

def generate_gemini(prompt_text: str, data: dict, out_dir: Path, ts: str) -> None:
    try:
        import google.generativeai as genai  # pip install google-generativeai
    except ImportError:
        sys.exit("[error] google-generativeai not installed. Run: pip install google-generativeai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("[error] GEMINI_API_KEY environment variable not set.")

    genai.configure(api_key=api_key)

    tech = data.get("technical", {})
    num_images = int(tech.get("num_images", 1))
    aspect_ratio = tech.get("aspect_ratio", "1:1")

    model = genai.ImageGenerationModel("imagen-3.0-generate-001")

    print(f"  [gemini] model=imagen-3.0-generate-001, images={num_images}, ratio={aspect_ratio}")

    response = model.generate_images(
        prompt=prompt_text,
        number_of_images=num_images,
        aspect_ratio=aspect_ratio,
        safety_filter_level="block_only_high",
        person_generation="allow_adult",
    )

    for i, img in enumerate(response.generated_images, start=1):
        img_bytes = base64.b64decode(img.image.image_bytes)
        save_image(out_dir, img_bytes, i, ts)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="nano-banana-skill image generator")
    parser.add_argument("prompt_file", help="Path to prompt JSON file")
    parser.add_argument(
        "--provider",
        choices=["fal", "gemini"],
        default="fal",
        help="Image generation provider (default: fal)",
    )
    args = parser.parse_args()

    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        sys.exit(f"[error] Prompt file not found: {prompt_path}")

    print(f"\nnano-banana-skill")
    print(f"  prompt  : {prompt_path}")
    print(f"  provider: {args.provider}\n")

    data = load_prompt(prompt_path)
    prompt_text = build_text_prompt(data)

    print(f"[prompt] {prompt_text}\n")

    campaign = data.get("meta", {}).get("campaign", "unnamed-campaign")
    out_dir = make_output_dir(campaign)
    ts = str(int(time.time()))

    save_prompt_snapshot(out_dir, data, ts)

    if args.provider == "fal":
        generate_fal(prompt_text, data, out_dir, ts)
    else:
        generate_gemini(prompt_text, data, out_dir, ts)

    print(f"\nDone. Output folder: {out_dir.relative_to(SKILL_ROOT)}\n")


if __name__ == "__main__":
    main()
