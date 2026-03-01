---
name: nano-banana-2-prompt-engineer
description: >
  Transforms plain-text image descriptions into structured JSON prompts optimized for Nano Banana 2
  (Gemini 3.1 Flash Image / gemini-3.1-flash-image-preview), then fires them to the API and saves
  results. Use this skill whenever the user wants to generate product shots, lifestyle images, ad
  creative, or brand visuals with Nano Banana 2. Trigger on: "generate image", "product shot",
  "lifestyle foto", "ad creative", "brand imagery", "fire to Nano Banana", "shoot this", or any
  request to create visuals for DTC brands, agencies, or marketing campaigns. Also trigger when
  user wants to iterate on existing image prompts or save prompt templates for reuse.
---

# Nano Banana 2 Prompt Engineer

Converts plain-text descriptions into precision-structured JSON prompts for Nano Banana 2,
maximizing consistency, photorealism, and brand alignment.

## Workflow

1. **Parse** the user's plain-text description
2. **Enrich** into structured JSON (see schema below)
3. **Load** matching style preset if one exists in `nano-banana-skill/styles/`
4. **Execute** via `nano-banana-skill/scripts/generate.py`
5. **Save** prompt JSON + image to `nano-banana-skill/output/YYYY-MM-DD/`
6. **Report** result + suggest iteration tweaks

---

## JSON Prompt Schema

```json
{
  "prompt": {
    "subject": "Exact product/subject description",
    "context": "Scene, environment, setting",
    "lighting": {
      "type": "natural | studio | golden hour | overcast | neon | etc.",
      "direction": "front | side | backlit | overhead | Rembrandt",
      "quality": "soft | hard | diffused | dramatic"
    },
    "camera": {
      "angle": "eye-level | low angle | bird's eye | Dutch tilt | overhead flat lay",
      "lens": "35mm | 50mm | 85mm | 100mm macro | 24mm wide",
      "depth_of_field": "shallow f/1.8 | medium f/5.6 | deep f/11",
      "shot_type": "close-up | medium | wide | detail macro"
    },
    "composition": {
      "rule": "rule of thirds | centered | golden ratio | negative space",
      "background": "Detailed background description",
      "props": ["prop 1", "prop 2"]
    },
    "style": {
      "aesthetic": "editorial | commercial | lifestyle | minimalist | luxury | raw",
      "color_grading": "warm tones | cool tones | muted | vibrant | monochrome",
      "mood": "aspirational | cozy | energetic | serene | bold"
    },
    "technical": {
      "resolution": "4K",
      "aspect_ratio": "1:1 | 4:5 | 16:9 | 9:16",
      "format": "png"
    },
    "negative_prompts": [
      "blurry", "plastic skin", "overexposed", "text artifacts",
      "distorted labels", "artificial looking", "harsh shadows"
    ]
  },
  "meta": {
    "campaign": "Campaign or project name",
    "style_preset": "preset name if used",
    "version": 1
  }
}
```

---

## Style Presets

Read from `nano-banana-skill/styles/` directory. Available presets:

- `styles/dtc-product.json` — Clean white/neutral product shots
- `styles/lifestyle-warm.json` — Golden hour lifestyle, aspirational
- `styles/luxury-editorial.json` — High-fashion, dramatic lighting
- `styles/flat-lay.json` — Overhead flat lay, minimal props

Load a preset by merging it with the user's prompt. User values override preset defaults.

---

## Iteration Protocol

After each generation:

1. Show the output image path
2. List 3 specific tweaks the user could make
3. Ask: "Wil je itereren op lighting, compositie, of stijl?"
4. On approval, bump `version` in meta and save new JSON alongside original

**Never overwrite** previous prompt JSONs — version them.

---

## API Configuration

Read from environment or ask user once:

- `GEMINI_API_KEY` — Google AI Studio key, OR
- `FAL_API_KEY` — fal.ai key (cheaper for volume, flat ~$0.03/image)

Model: `gemini-3.1-flash-image-preview` (Nano Banana 2)

See `nano-banana-skill/scripts/generate.py` for full implementation.
For API setup instructions: read `nano-banana-skill/references/api-setup.md`

---

## Instructions for Claude

When this skill is triggered:

1. Ask the user for their plain-text description if not provided.
2. Convert it to the JSON schema above — be specific and cinematic with every field.
3. Infer a `style_preset` if the request matches one (e.g. "clean white" → `dtc-product`,
   "golden hour" → `lifestyle-warm`, "editorial" → `luxury-editorial`, "overhead" → `flat-lay`).
4. Write the prompt JSON to `nano-banana-skill/<campaign-slug>_v<version>.json`.
5. Run: `python nano-banana-skill/scripts/generate.py <file> --provider gemini`
6. Report the output path and suggest 3 concrete iteration options.
7. On iteration: load the previous JSON, apply changes, bump version, save new file, regenerate.
