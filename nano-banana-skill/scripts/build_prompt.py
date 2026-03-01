#!/usr/bin/env python3
"""
build_prompt.py — Interactive CLI wizard for Nano Banana 2 prompt schema.

Outputs the new structured JSON format:
  { "prompt": { subject, context, lighting, camera, composition, style, technical, negative_prompts },
    "meta": { campaign, style_preset, version } }

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
    return sorted(p.stem for p in STYLES_DIR.glob("*.json"))


def build() -> dict:
    print("\n" + "=" * 60)
    print("  Nano Banana 2 — Prompt Builder")
    print("=" * 60 + "\n")

    # --- META ---
    print("[ Campaign ]")
    campaign = ask("Campaign name (used as output folder)", required=True)
    version = 1

    presets = available_presets()
    print(f"\n[ Style Preset ]  (available: {', '.join(presets) or 'none found'})")
    use_preset = ask_choice("Use a style preset?", ["yes", "no"], default="no")
    style_preset = ""
    if use_preset == "yes" and presets:
        style_preset = ask_choice("Preset name", presets, default=presets[0])

    # --- SUBJECT & CONTEXT ---
    print("\n[ Subject & Scene ]")
    subject = ask("Subject — exact product/object description", required=True)
    context = ask("Context — scene, environment, setting", default="studio setting")

    # --- LIGHTING ---
    print("\n[ Lighting ]")
    light_type = ask(
        "Type",
        default="studio",
    )
    light_direction = ask_choice(
        "Direction",
        ["front", "side", "backlit", "overhead", "Rembrandt"],
        default="front",
    )
    light_quality = ask_choice(
        "Quality",
        ["soft", "hard", "diffused", "dramatic"],
        default="soft",
    )

    # --- CAMERA ---
    print("\n[ Camera ]")
    shot_type = ask_choice(
        "Shot type",
        ["close-up", "medium", "wide", "detail macro"],
        default="medium",
    )
    angle = ask_choice(
        "Angle",
        ["eye-level", "low angle", "bird's eye", "Dutch tilt", "overhead flat lay"],
        default="eye-level",
    )
    lens = ask_choice(
        "Lens",
        ["35mm", "50mm", "85mm", "100mm macro", "24mm wide"],
        default="85mm",
    )
    dof = ask_choice(
        "Depth of field",
        ["shallow f/1.8", "medium f/5.6", "deep f/11"],
        default="shallow f/1.8",
    )

    # --- COMPOSITION ---
    print("\n[ Composition ]")
    rule = ask_choice(
        "Compositional rule",
        ["rule of thirds", "centered", "golden ratio", "negative space"],
        default="rule of thirds",
    )
    background = ask("Background description", default="white seamless")
    props = ask_list("Props (supporting elements)")

    # --- STYLE ---
    print("\n[ Style ]")
    aesthetic = ask_choice(
        "Aesthetic",
        ["editorial", "commercial", "lifestyle", "minimalist", "luxury", "raw"],
        default="commercial",
    )
    color_grading = ask_choice(
        "Color grading",
        ["warm tones", "cool tones", "muted", "vibrant", "monochrome"],
        default="warm tones",
    )
    mood = ask_choice(
        "Mood",
        ["aspirational", "cozy", "energetic", "serene", "bold"],
        default="aspirational",
    )

    # --- TECHNICAL ---
    print("\n[ Technical ]")
    aspect_ratio = ask_choice(
        "Aspect ratio",
        ["1:1", "4:5", "16:9", "9:16"],
        default="1:1",
    )
    num_images = ask("Number of images", default="1")
    try:
        num_images = max(1, min(8, int(num_images)))
    except ValueError:
        num_images = 1

    # --- NEGATIVE PROMPTS ---
    print("\n[ Negative Prompts ]")
    default_negatives = "blurry, plastic look, overexposed, text artifacts, distorted labels"
    print(f"  Defaults: {default_negatives}")
    extra_negatives = ask_list("Additional negatives to add (comma-separated)")
    negative_prompts = [s.strip() for s in default_negatives.split(",")]
    negative_prompts.extend(extra_negatives)

    # --- ASSEMBLE ---
    data: dict = {
        "prompt": {
            "subject": subject,
            "context": context,
            "lighting": {
                "type": light_type,
                "direction": light_direction,
                "quality": light_quality,
            },
            "camera": {
                "angle": angle,
                "lens": lens,
                "depth_of_field": dof,
                "shot_type": shot_type,
            },
            "composition": {
                "rule": rule,
                "background": background,
            },
            "style": {
                "aesthetic": aesthetic,
                "color_grading": color_grading,
                "mood": mood,
            },
            "technical": {
                "resolution": "4K",
                "aspect_ratio": aspect_ratio,
                "num_images": num_images,
                "format": "png",
            },
            "negative_prompts": negative_prompts,
        },
        "meta": {
            "campaign": campaign,
            "version": version,
        },
    }

    if style_preset:
        data["meta"]["style_preset"] = style_preset
    if props:
        data["prompt"]["composition"]["props"] = props

    return data


def main() -> None:
    data = build()

    campaign = data["meta"]["campaign"]
    version = data["meta"]["version"]
    slug = campaign.lower().replace(" ", "-")
    out_path = SKILL_ROOT / f"{slug}_v{version}.json"

    print(f"\n[ Preview ]\n{json.dumps(data, indent=2)}\n")

    confirm = input(f"Save to {out_path.name}? [Y/n]: ").strip().lower()
    if confirm not in ("", "y", "yes"):
        print("\nAborted — nothing saved.")
        sys.exit(0)

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved: {out_path.name}")
    print(f"\nNext step:")
    print(f"  python scripts/generate.py {out_path.name} --provider gemini --model flash\n")


if __name__ == "__main__":
    main()
