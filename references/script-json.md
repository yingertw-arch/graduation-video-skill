# script.json Reference

`script.json` is the renderer contract. Keep media paths relative to the material folder.

## Top-level fields

Required: `title`, `mode`, `output`, `width`, `height`, `scenes`.

```json
{
  "title": "2026 畢業回憶",
  "mode": "subtitle-only",
  "voice": "zh-TW-HsiaoChenNeural",
  "output": "graduation_video.mp4",
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "font": "C:/Windows/Fonts/msjh.ttc",
  "font_size": 42,
  "duration_per_image": 5,
  "visual_profile": "warm_cinematic",
  "safe_area": {"subtitle_bottom": 120, "title_margin": 160},
  "audio": {"bgm_volume": 0.25, "tts_volume": 1.0, "sound_cues": false},
  "scenes": []
}
```

`mode`: `voice` or `subtitle-only`.

## Scene

```json
{
  "id": 1,
  "name": "準備出發",
  "story_role": "setup",
  "rhythm": "documentary",
  "color_look": "bright_documentary",
  "chapter_marker": {"text": "準備出發", "style": "lower_third_line"},
  "media": []
}
```

Scene IDs must be unique. Suggested story roles: `hook`, `setup`, `peak`, `turn`, `echo`.

## Title card

```json
{
  "type": "titlecard",
  "template": "cinematic_blur",
  "background_file": "IMG_0001.jpg",
  "title": "我們畢業了",
  "subtitle": "海山國小 603 班",
  "kicker": "Graduation 2026",
  "duration": 5,
  "motion": "slow_push_in",
  "color_look": "warm_cinematic",
  "sound_cue": "soft_hit"
}
```

Legacy title card is also valid:

```json
{"type": "titlecard", "text": "我們畢業了", "duration": 3}
```

## Photo or video item

```json
{
  "file": "IMG_001.jpg",
  "narration": "今天，我們帶著笑容和勇氣，走向下一段旅程。",
  "duration": 5,
  "layout": "photo_stack",
  "motion": "slow_push_in",
  "effect": "zoom-in",
  "style": "vibrant",
  "frame": "thin_white",
  "transition": "dissolve",
  "sound_cue": "none"
}
```

For videos, use `layout: "letterbox_video"` for vertical or non-16:9 clips and `style: "none"` unless the renderer supports video filters.

## Allowed values

- `visual_profile` / `color_look`: `warm_cinematic`, `bright_documentary`, `lively_school`, `ceremony_gold`, `soft_pastel`, `natural`
- `story_role`: `hook`, `setup`, `peak`, `turn`, `echo`
- `rhythm`: `warm_slow`, `lively_fast`, `cinematic_peak`, `emotional_pause`, `documentary`
- `layout`: `full_bleed`, `photo_stack`, `split_two`, `scrapbook`, `film_frame`, `detail_focus`, `letterbox_video`
- `motion`: `slow_push_in`, `slow_pull_back`, `pan_right`, `pan_left`, `parallax_soft`, `handheld_soft`, `none`
- `effect`: `zoom-in`, `pan-right`, `pan-left`, `none`
- `style`: `vibrant`, `vintage`, `sepia`, `film`, `bw`, `none`
- `frame`: `polaroid`, `film_strip`, `thin_white`, `shadow_card`, `none`
- `transition`: `dissolve`, `slide_left`, `slide_right`, `zoom_cut`, `whip_pan`, `flash_white`, `match_cut`, `fade`
- `titlecard.template`: `cinematic_blur`, `paper_memory`, `ceremony_gold`, `clean_documentary`, `chalkboard`
- `chapter_marker.style`: `lower_third_line`, `date_stamp`, `small_badge`, `none`
- `sound_cue`: `soft_hit`, `soft_whoosh`, `beat_hit`, `camera_click`, `none`

## Duration heuristics

- Opening and closing title cards: 4-6 seconds.
- Subtitle-only photos: usually 4-6 seconds.
- Voice mode: keep narration concise; about 12-18 Chinese characters per 3 seconds.
- Peak scenes: 2.5-4 seconds per image.
- Reflection scenes: 5-7 seconds per image.
- Keep estimated total within 15% of target duration.
