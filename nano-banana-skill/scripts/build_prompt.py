#!/usr/bin/env python3
"""
build_prompt.py — Interactive CLI wizard to build a prompt JSON file.

Usage:
    python scripts/build_prompt.py
"""

import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).parent.parent
STYLES_DIR = SKILL_ROOT / "styles"


def ask(label: str, default: str = "", required: bool = False) -> str:
    hint = f" [{default}]" if default else ""
    while True:
        value = input(f"  {label}{hint}: ").strip()
        if not value:
            if required:
                print("    (required — please enter a value)")
                continue
            return default
        return value


def ask_list(label: str, hint: str = "comma-separated, leave empty to skip") -> list:
    raw = input(f"  {label} ({hint}): ").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def ask_choice(label: str, choices: list, default: str = "") -> str:
    options = " | ".join(choices)
    hint = f" [{default}]" if default else f" [{choices[0]}]"
    while True:
        value = input(f"  {label} ({options}){hint}: ").strip()
        if not value:
            return default or choices[0]
        if value in choices:
            return value
        print(f"    Choose one of: {options}")


def available_presets() -> list:
    presets = [p.stem for p in STYLES_DIR.glob("*.json")]
    return sorted(presets)


def build() -> dict:
    print("\n" + "=" * 60)
    print("  nano-banana-skill — Interactive Prompt Builder")
    print("=" * 60 + "\n")

    # --- META ---
    print("[ Campaign ]")
    campaign = ask("Campaign name (used as output folder)", required=True)

    presets = available_presets()
    print(f"\n[ Style Preset ]  (available: {', '.join(presets) or 'none'})")
    use_preset = ask_choice("Use a style preset?", ["yes", "no"], default="no")
    style_preset = ""
    if use_preset == "yes" and presets:
        style_preset = ask_choice("Preset name", presets, default=presets[0])

    # --- PRODUCT ---
    print("\n[ Product ]")
    name = ask("Product name", required=True)
    category = ask("Category (e.g. skincare serum, sneaker, coffee mug)", required=True)
    color = ask("Color & finish (e.g. matte black, amber glass)", default="")
    material = ask("Material & size (e.g. 30ml glass bottle, canvas tote)", default="")
    features = ask_list("Key visible features")

    # --- SHOT ---
    print("\n[ Shot ]")
    angle = ask("Camera angle", default="45-degree front-facing")
    background = ask("Background", default="white seamless")
    lighting = ask("Lighting description", default="soft studio light from upper left")
    props = ask_list("Props (supporting elements)")
    mood = ask("Mood / atmosphere", default="clean and minimal")

    # --- TECHNICAL ---
    print("\n[ Technical ]")
    aspect_ratio = ask_choice(
        "Aspect ratio", ["1:1", "4:3", "16:9", "9:16"], default="1:1"
    )
    num_images = ask("Number of images to generate", default="4")
    try:
        num_images = max(1, min(8, int(num_images)))
    except ValueError:
        num_images = 4

    quality = ask_choice("Quality", ["standard", "hd"], default="hd")

    # --- ASSEMBLE ---
    data: dict = {
        "meta": {"campaign": campaign},
        "product": {
            "name": name,
            "category": category,
        },
        "shot": {
            "angle": angle,
            "background": background,
            "lighting": lighting,
            "mood": mood,
        },
        "technical": {
            "aspect_ratio": aspect_ratio,
            "num_images": num_images,
            "quality": quality,
        },
    }

    if style_preset:
        data["meta"]["style_preset"] = style_preset
    if color:
        data["product"]["color"] = color
    if material:
        data["product"]["material"] = material
    if features:
        data["product"]["key_features"] = features
    if props:
        data["shot"]["props"] = props

    return data


def main() -> None:
    data = build()

    slug = data["meta"]["campaign"].lower().replace(" ", "-")
    out_path = SKILL_ROOT / f"{slug}.json"

    print(f"\n[ Preview ]\n{json.dumps(data, indent=2)}\n")

    confirm = input(f"Save to {out_path.name}? [Y/n]: ").strip().lower()
    if confirm in ("", "y", "yes"):
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved: {out_path.relative_to(SKILL_ROOT.parent)}")
        print(f"\nNext step:")
        print(f"  python scripts/generate.py {out_path.name} --provider fal\n")
    else:
        print("\nAborted — nothing saved.")
        sys.exit(0)


if __name__ == "__main__":
    main()
