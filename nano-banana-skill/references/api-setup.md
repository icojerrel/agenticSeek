# API Setup — nano-banana-skill

Two providers are supported: **fal.ai** (recommended) and **Google Gemini Imagen**.

---

## fal.ai (Flux)

### 1. Get an API key

1. Sign up at https://fal.ai
2. Go to **Dashboard → API Keys → Create key**
3. Copy the key

### 2. Install the client

```bash
pip install fal-client
```

### 3. Export the key

```bash
export FAL_API_KEY=your_key_here
```

Or add it permanently to your shell profile (`~/.zshrc` / `~/.bashrc`):

```bash
echo 'export FAL_API_KEY=your_key_here' >> ~/.zshrc
```

### Models used

| Quality setting | Model |
|-----------------|-------|
| `standard` | `fal-ai/flux/dev` |
| `hd` | `fal-ai/flux-pro` |

### Rate limits & pricing (as of early 2025)

- Flux Dev: ~$0.025 per image
- Flux Pro: ~$0.05 per image
- No hard rate limit on paid plans; free tier: 30 credits/month

---

## Google Gemini Imagen

### 1. Get an API key

1. Go to https://aistudio.google.com
2. Click **Get API key → Create API key**
3. Copy the key

### 2. Install the SDK

```bash
pip install google-generativeai
```

### 3. Export the key

```bash
export GEMINI_API_KEY=your_key_here
```

### Model used

`imagen-3.0-generate-001`

### Rate limits & pricing (as of early 2025)

- Free tier: 15 requests per minute (RPM), limited to 60/day
- Paid tier: $0.02 per image
- Imagen 3 is available in all regions that support the Gemini API

---

## Choosing a provider

| | fal.ai | Gemini Imagen |
|---|---|---|
| Image quality | Excellent (Flux Pro) | Very good |
| Speed | Fast (~5–15s) | Moderate (~10–20s) |
| Free tier | 30 credits/mo | 60 images/day |
| Best for | Creative/editorial shots | Photorealistic product |
| Aspect ratios | All 4 supported | All 4 supported |

---

## Troubleshooting

**`fal_client` not found**
```bash
pip install fal-client
```

**`google.generativeai` not found**
```bash
pip install google-generativeai
```

**API key not set error**
```bash
echo $FAL_API_KEY        # should print your key
echo $GEMINI_API_KEY     # should print your key
```

**Image generation fails with safety filter**

Gemini Imagen has stricter filters. Rephrase the prompt to be less
ambiguous — avoid words that could be misread as violent, medical, or adult.
The `safety_filter_level="block_only_high"` setting is already applied in
`generate.py` to minimise false positives.
