# nano-banana-skill — AI Product Photography Generator

Generate professional AI product images from structured JSON prompts.
Supports fal.ai and Google Gemini Imagen backends, with versioned output and style presets.

---

## Quick Start

```bash
# Export your API key
export FAL_API_KEY=your_key_here
# or
export GEMINI_API_KEY=your_key_here

# Interactive prompt builder
python scripts/build_prompt.py

# Generate from an existing prompt file
python scripts/generate.py example_prompt.json --provider fal

# Generate with a style preset
# Add to your JSON: "meta": { "style_preset": "lifestyle-warm" }
python scripts/generate.py my_product.json --provider gemini
```

---

## Prompt JSON Schema

```json
{
  "meta": {
    "campaign": "string — folder name for output",
    "style_preset": "string — optional: dtc-product | lifestyle-warm | luxury-editorial | flat-lay"
  },
  "product": {
    "name": "string",
    "category": "string",
    "color": "string",
    "material": "string",
    "key_features": ["string"]
  },
  "shot": {
    "angle": "string — e.g. front-facing, 45-degree, overhead",
    "background": "string",
    "lighting": "string",
    "props": ["string — optional supporting elements"],
    "mood": "string"
  },
  "technical": {
    "aspect_ratio": "1:1 | 4:3 | 16:9 | 9:16",
    "num_images": 1,
    "quality": "standard | hd"
  }
}
```

---

## Style Presets

| Preset | Description |
|--------|-------------|
| `dtc-product` | Clean white/grey studio — sharp shadows, e-commerce ready |
| `lifestyle-warm` | Golden hour, natural textures, aspirational feel |
| `luxury-editorial` | Dramatic lighting, deep blacks, high-fashion editorial |
| `flat-lay` | Overhead minimal, pastel or marble surface |

Presets merge with your prompt JSON — your explicit values always win.

---

## Output Structure

```
output/
└── YYYY-MM-DD/
    └── <campaign-name>/
        ├── prompt_<timestamp>.json   ← exact prompt used
        ├── image_1_<timestamp>.png
        ├── image_2_<timestamp>.png
        └── ...
```

Every run is non-destructive — timestamps prevent overwrites so you can iterate freely.

---

## Providers

| Provider | Env var | Models used |
|----------|---------|-------------|
| fal.ai | `FAL_API_KEY` | `fal-ai/flux/dev`, `fal-ai/flux-pro` |
| Google Gemini | `GEMINI_API_KEY` | `imagen-3.0-generate-001` |

See `references/api-setup.md` for key acquisition and rate limits.

---

## Files

```
nano-banana-skill/
├── SKILL.md                  ← This file
├── example_prompt.json       ← Skincare product example
├── scripts/
│   ├── generate.py           ← Main pipeline: JSON → API → save
│   └── build_prompt.py       ← Interactive prompt builder (CLI wizard)
├── styles/
│   ├── dtc-product.json
│   ├── lifestyle-warm.json
│   ├── luxury-editorial.json
│   └── flat-lay.json
├── references/
│   └── api-setup.md
└── output/                   ← Generated images land here (git-ignored)
```
