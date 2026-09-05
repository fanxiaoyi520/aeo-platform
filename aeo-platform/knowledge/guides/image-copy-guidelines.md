# Image Copy Guidelines

> MV2-04 — A03 listing extension: main image callouts + scene image copywriting.

## Overview

Image copy agent produces two types of output for product listing images:

1. **Main image copy** — short callout labels, badge text, compliance note
2. **Scene image copy** — scene descriptions, lifestyle copy, mood tags

## Main Image

### Callouts

- Exactly **3** callout strings
- Each callout **≤ 10 characters** (including spaces)
- Should highlight key product features or selling points
- Examples: "防水", "蓝牙5.3", "降噪", "32H续航", "IPX5"

### Badge Text

- Short promotional badge (e.g., "热销爆款", "新品首发", "限时特惠")
- Should create urgency or highlight uniqueness

### Compliance Note

- Required disclaimers or notes (e.g., "结果因使用环境而异", "颜色可能略有差异")
- Platform-specific requirements apply

## Scene Images

### Scene Description

- Exactly **3** scene entries
- Each description **≤ 30 characters**
- Describe the usage scenario or lifestyle context
- Examples: "地铁上享受安静音乐", "开放式办公专注利器"

### Lifestyle Copy

- Punchy marketing copy that connects product to lifestyle
- Should evoke emotion or aspiration
- Examples: "通勤也能很享受", "效率翻倍不是梦"

### Mood

- Single-word mood descriptor
- Examples: "relaxed", "focused", "energetic", "adventurous"

## Platform Differences

| Aspect | Amazon | TikTok |
|--------|--------|--------|
| Tone | Professional, informative | Trendy, casual |
| Callout style | Feature-focused | Benefit-focused |
| Scene style | Practical use cases | Lifestyle/aspirational |

## Output Schema

```json
{
  "main_image": {
    "callouts": ["string ≤10 chars", "string ≤10 chars", "string ≤10 chars"],
    "badge_text": "string",
    "compliance_note": "string"
  },
  "scene_images": [
    {
      "scene": "scene name",
      "description": "string ≤30 chars",
      "lifestyle_copy": "marketing copy",
      "mood": "single word"
    }
  ]
}
```

## Integration

- Graph: `build_image_copy_graph()` in `aeo_orchestrator.graph`
- Runner: `run_image_copy_task()` in `aeo_orchestrator.runner`
- Agent: `image_copy_agent` (category: LISTING, capability: `generate.image_copy`)
