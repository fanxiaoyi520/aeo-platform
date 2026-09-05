# TikTok Short Video Script & Storyboard Guidelines

## Output Schema

```json
{
  "script": {
    "hook": "string ≤20 chars — attention-grabbing opening",
    "selling_points": ["string ≤15 chars", "...", "..."],
    "cta": "string — call-to-action",
    "duration_seconds": 15 | 30 | 60
  },
  "storyboard": [
    {
      "shot": 1,
      "visual": "string ≤40 chars — camera description",
      "duration": "5s",
      "subtitle": "string — on-screen text",
      "bgm_mood": "energetic | relaxed | funny | dramatic | trendy"
    }
  ],
  "platform": "tiktok"
}
```

## Platform Rules

- Hook must grab attention in the first 1-2 seconds
- Selling points: max 3, each ≤15 characters
- Storyboard: 3-5 shots, each with visual + duration + subtitle + BGM mood
- Target durations: 15s (quick hit), 30s (standard), 60s (detailed)
- Tone: trendy, casual, relatable — not corporate
- Subtitles are critical (most users watch with sound off initially)

## Integration Points

- **Input**: product_info, generated listing (title + bullets), research data, image_copy
- **Output key**: `tiktok_video` in TaskState
- **Agent**: `tiktok_video_agent` (A03 LISTING category)
- **Graph**: `tiktok_video` sub-graph (single node)
