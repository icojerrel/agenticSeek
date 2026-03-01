#!/usr/bin/env python3
"""
generate.py — nano-banana-skill / Nano Banana 2 pipeline

Supports two JSON schemas:
  - New (Nano Banana 2): { "prompt": { subject, context, lighting, camera, ... }, "meta": {...} }
  - Legacy:              { "product": {...}, "shot": {...}, "technical": {...}, "meta": {...} }

Usage:
    python scripts/generate.py <prompt.json> --provider fal
    python scripts/generate.py <prompt.json> --provider gemini
    python scripts/generate.py <prompt.json> --provider gemini --model flash --count 2
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
STYLES_DIR = SKILL_ROOT / "styles"
OUTPUT_DIR = SKILL_ROOT / "output"

GEMINI_FLASH_MODEL = "gemini-3.1-flash-image-preview"
GEMINI_IMAGEN_MODEL = "imagen-3.0-generate-001"


# ---------------------------------------------------------------------------
# Prompt loading + preset merge
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


# ---------------------------------------------------------------------------
# Text prompt construction (new schema + legacy schema)
# ---------------------------------------------------------------------------

def build_text_prompt(data: dict) -> tuple[str, str | None]:
    """Return (positive_prompt, negative_prompt_or_None)."""
    if "prompt" in data:
        return _build_from_new_schema(data["prompt"])
    return _build_from_legacy_schema(data), None


def _build_from_new_schema(p: dict) -> tuple[str, str | None]:
    parts = []

    if p.get("subject"):
        parts.append(p["subject"] + ".")

    if p.get("context"):
        parts.append(p["context"] + ".")

    lighting = p.get("lighting", {})
    if lighting:
        parts.append(
            f"Lighting: {lighting.get('type', 'natural')} from {lighting.get('direction', 'front')}, "
            f"{lighting.get('quality', 'soft')}."
        )

    camera = p.get("camera", {})
    if camera:
        parts.append(
            f"Camera: {camera.get('shot_type', 'medium shot')} with {camera.get('lens', '50mm')}, "
            f"{camera.get('angle', 'eye-level')}, {camera.get('depth_of_field', 'medium f/5.6')}."
        )

    composition = p.get("composition", {})
    if composition:
        bg = composition.get("background", "")
        rule = composition.get("rule", "")
        props = composition.get("props", [])
        comp_str = f"Composition: {rule}" if rule else "Composition:"
        if bg:
            comp_str += f", {bg} background"
        if props:
            comp_str += f". Props: {', '.join(props)}"
        parts.append(comp_str + ".")

    style = p.get("style", {})
    if style:
        parts.append(
            f"Aesthetic: {style.get('aesthetic', 'commercial')}, "
            f"{style.get('color_grading', 'natural tones')}, "
            f"{style.get('mood', 'clean')}."
        )

    tech = p.get("technical", {})
    if tech.get("resolution"):
        parts.append(f"{tech['resolution']}, photorealistic, commercial quality, sharp focus.")
    else:
        parts.append("Photorealistic, commercial quality, sharp focus.")

    negative = None
    neg_list = p.get("negative_prompts", [])
    if neg_list:
        negative = ", ".join(neg_list)

    return " ".join(parts), negative


def _build_from_legacy_schema(data: dict) -> str:
    p = data.get("product", {})
    s = data.get("shot", {})

    props_str = f" Props: {', '.join(s['props'])}." if s.get("props") else ""
    features_str = (
        f" Features visible: {', '.join(p['key_features'])}." if p.get("key_features") else ""
    )

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


def _get_tech(data: dict) -> dict:
    """Return the technical block regardless of schema version."""
    if "prompt" in data:
        return data["prompt"].get("technical", {})
    return data.get("technical", {})


# ---------------------------------------------------------------------------
# fal.ai provider
# ---------------------------------------------------------------------------

def generate_fal(prompt_text: str, data: dict, out_dir: Path, ts: str, count: int) -> None:
    try:
        import fal_client
    except ImportError:
        sys.exit("[error] fal-client not installed. Run: pip install fal-client")

    if not os.environ.get("FAL_API_KEY"):
        sys.exit("[error] FAL_API_KEY environment variable not set.")

    tech = _get_tech(data)
    aspect_ratio = tech.get("aspect_ratio", "1:1")
    quality = tech.get("quality", "hd")
    model = "fal-ai/flux-pro" if quality == "hd" else "fal-ai/flux/dev"

    print(f"  [fal] model={model}, images={count}, ratio={aspect_ratio}")

    result = fal_client.run(
        model,
        arguments={
            "prompt": prompt_text,
            "num_images": count,
            "image_size": _fal_image_size(aspect_ratio),
            "num_inference_steps": 28 if quality == "hd" else 20,
        },
    )

    for i, img_obj in enumerate(result.get("images", []), start=1):
        tmp_path, _ = urllib.request.urlretrieve(img_obj["url"])
        with open(tmp_path, "rb") as f:
            save_image(out_dir, f.read(), i, ts)


def _fal_image_size(aspect_ratio: str) -> str:
    return {
        "1:1": "square_hd",
        "4:3": "landscape_4_3",
        "4:5": "portrait_4_5",
        "16:9": "landscape_16_9",
        "9:16": "portrait_16_9",
    }.get(aspect_ratio, "square_hd")


# ---------------------------------------------------------------------------
# Google Gemini provider — Flash Image (Nano Banana 2) + Imagen fallback
# ---------------------------------------------------------------------------

def generate_gemini(
    prompt_text: str,
    negative_prompt: str | None,
    data: dict,
    out_dir: Path,
    ts: str,
    count: int,
    model_variant: str,
) -> None:
    try:
        import google.generativeai as genai
    except ImportError:
        sys.exit("[error] google-generativeai not installed. Run: pip install google-generativeai")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("[error] GEMINI_API_KEY environment variable not set.")

    genai.configure(api_key=api_key)

    tech = _get_tech(data)
    aspect_ratio = tech.get("aspect_ratio", "1:1")

    if model_variant == "flash":
        _generate_gemini_flash(genai, prompt_text, out_dir, ts, count, aspect_ratio)
    else:
        _generate_gemini_imagen(genai, prompt_text, out_dir, ts, count, aspect_ratio)


def _generate_gemini_flash(genai, prompt_text: str, out_dir: Path, ts: str, count: int, aspect_ratio: str) -> None:
    """Nano Banana 2: gemini-3.1-flash-image-preview via generate_content."""
    print(f"  [gemini] model={GEMINI_FLASH_MODEL}, images={count}, ratio={aspect_ratio}")

    model = genai.GenerativeModel(GEMINI_FLASH_MODEL)

    for i in range(1, count + 1):
        response = model.generate_content(
            prompt_text,
            generation_config=genai.GenerationConfig(
                response_modalities=["image"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data:
                img_bytes = part.inline_data.data
                # data may already be bytes or b64-encoded depending on SDK version
                if isinstance(img_bytes, str):
                    img_bytes = base64.b64decode(img_bytes)
                save_image(out_dir, img_bytes, i, ts)
                break
        else:
            print(f"  [warn] no image in response for image {i}")


def _generate_gemini_imagen(genai, prompt_text: str, out_dir: Path, ts: str, count: int, aspect_ratio: str) -> None:
    """Imagen 3 fallback via ImageGenerationModel."""
    print(f"  [gemini] model={GEMINI_IMAGEN_MODEL}, images={count}, ratio={aspect_ratio}")

    model = genai.ImageGenerationModel(GEMINI_IMAGEN_MODEL)
    response = model.generate_images(
        prompt=prompt_text,
        number_of_images=count,
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
    parser = argparse.ArgumentParser(description="nano-banana-skill / Nano Banana 2 image generator")
    parser.add_argument("prompt_file", help="Path to prompt JSON file")
    parser.add_argument(
        "--provider",
        choices=["fal", "gemini"],
        default="gemini",
        help="Image generation provider (default: gemini)",
    )
    parser.add_argument(
        "--model",
        choices=["flash", "imagen"],
        default="flash",
        help="Gemini model variant: 'flash' = gemini-3.1-flash-image-preview (Nano Banana 2), "
             "'imagen' = imagen-3.0-generate-001 (default: flash)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of images to generate (overrides JSON; default: 1 for flash, from JSON for others)",
    )
    args = parser.parse_args()

    prompt_path = Path(args.prompt_file)
    if not prompt_path.exists():
        sys.exit(f"[error] Prompt file not found: {prompt_path}")

    print(f"\nnano-banana-skill — Nano Banana 2")
    print(f"  prompt  : {prompt_path}")
    print(f"  provider: {args.provider}")
    if args.provider == "gemini":
        model_label = GEMINI_FLASH_MODEL if args.model == "flash" else GEMINI_IMAGEN_MODEL
        print(f"  model   : {model_label}")
    print()

    data = load_prompt(prompt_path)
    positive, negative = build_text_prompt(data)

    print(f"[prompt] {positive}")
    if negative:
        print(f"[negative] {negative}")
    print()

    # Resolve image count: CLI flag > JSON technical.num_images > 1
    tech = _get_tech(data)
    count = args.count or int(tech.get("num_images", 1))

    campaign = data.get("meta", {}).get("campaign", "unnamed-campaign")
    out_dir = make_output_dir(campaign)
    ts = str(int(time.time()))

    save_prompt_snapshot(out_dir, data, ts)

    if args.provider == "fal":
        generate_fal(positive, data, out_dir, ts, count)
    else:
        generate_gemini(positive, negative, data, out_dir, ts, count, args.model)

    print(f"\nDone. Output: {out_dir.relative_to(SKILL_ROOT)}\n")


if __name__ == "__main__":
    main()
