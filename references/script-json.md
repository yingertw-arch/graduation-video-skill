# script.json Reference

Use this reference when creating or editing the video script. The schema is backward-compatible with the simple slideshow renderer, but adds professional design fields for upgraded renderers.

## Top-Level Shape

```json
{
  "title": "Graduation 2026",
  "mode": "voice",
  "voice": "zh-TW-HsiaoChenNeural",
  "output": "Graduation 2026.mp4",
  "width": 1920,
  "height": 1080,
  "fps": 24,
  "font": "C:/Windows/Fonts/msjh.ttc",
  "font_size": 42,
  "duration_per_image": 5,
  "visual_profile": "warm_cinematic",
  "safe_area": {
    "subtitle_bottom": 120,
    "title_margin": 160
  },
  "audio": {
    "bgm_volume": 0.28,
    "tts_volume": 1.0,
    "sound_cues": true
  },
  "scenes": []
}
```

Required fields: `title`, `mode`, `output`, `width`, `height`, `scenes`.

`mode` must be `voice` or `subtitle-only`.

Use relative media filenames from the material folder. Avoid absolute paths in `media.file`.

## Scene Shape

```json
{
  "id": 1,
  "name": "Getting Ready",
  "story_role": "setup",
  "rhythm": "warm_slow",
  "color_look": "warm_cinematic",
  "chapter_marker": {
    "text": "Getting Ready",
    "style": "lower_third_line"
  },
  "media": []
}
```

Scene IDs should be unique. Use `0` for opening title card and `99` for closing title card when convenient.

## Motion Title Cards

Prefer this shape for opening and closing titles:

```json
{
  "type": "titlecard",
  "template": "cinematic_blur",
  "background_file": "IMG_0001.jpg",
  "title": "??箇",
  "subtitle": "Haishan Elementary Class 603",
  "kicker": "Graduation 2026",
  "duration": 5,
  "motion": "slow_push_in",
  "color_look": "warm_cinematic",
  "sound_cue": "soft_hit"
}
```

Legacy title cards are still valid:

```json
{
  "type": "titlecard",
  "text": "??箇",
  "duration": 3
}
```

## Media Items

Photo item:

```json
{
  "file": "IMG_001.jpg",
  "narration": "Today, we set out together and carried our courage into the next chapter.",
  "duration": 5,
  "layout": "photo_stack",
  "motion": "slow_push_in",
  "effect": "zoom-in",
  "style": "vibrant",
  "frame": "polaroid",
  "transition": "dissolve",
  "sound_cue": "soft_whoosh"
}
```

Video item:

```json
{
  "file": "MVI_001.mp4",
  "narration": "The children focused on the challenge and cheered one another on.",
  "layout": "full_bleed",
  "motion": "none",
  "effect": "none",
  "style": "none",
  "frame": "none",
  "transition": "zoom_cut",
  "sound_cue": "beat_hit"
}
```

## Allowed Values

Top-level `visual_profile` and scene/media `color_look`:

| Value | Use |
| --- | --- |
| `warm_cinematic` | Graduation, memories, warm ceremony tone |
| `bright_documentary` | Teaching records, clean classroom documentation |
| `lively_school` | Field trips, activities, colorful energy |
| `ceremony_gold` | Formal school ceremony, awards, anniversary |
| `soft_pastel` | Cute lower-grade activities |
| `natural` | Minimal grading |

`story_role`:

| Value | Use |
| --- | --- |
| `hook` | Opening attention |
| `setup` | Preparation/context |
| `peak` | Best highlights |
| `turn` | Reflection/emotional shift |
| `echo` | Closing memory |

`rhythm`:

| Value | Use |
| --- | --- |
| `warm_slow` | Gentle memories, graduation |
| `lively_fast` | Games, field trips, celebration |
| `cinematic_peak` | Best moments, applause, performance |
| `emotional_pause` | Farewell, gratitude, reflection |
| `documentary` | Teaching records, process explanation |

`layout`:

| Value | Use |
| --- | --- |
| `full_bleed` | Strong single image or video |
| `photo_stack` | Memory collage, portraits, groups |
| `split_two` | Compare two moments or show pair images |
| `scrapbook` | Warm class-memory style |
| `film_frame` | Dynamic highlights |
| `detail_focus` | Object/detail closeups |
| `letterbox_video` | Vertical or non-16:9 video clips |

`motion`:

| Value | Use |
| --- | --- |
| `slow_push_in` | Premium title, emotional photo |
| `slow_pull_back` | Reveal group/context |
| `pan_right` | Journey, moving forward |
| `pan_left` | Looking back |
| `parallax_soft` | Pro layered photo feel when supported |
| `handheld_soft` | Lively documentary movement when supported |
| `none` | Video clips or static |

Legacy `effect`:

| Value | Use |
| --- | --- |
| `zoom-in` | Focus attention, portraits, key moments |
| `pan-right` | Departure, movement, journey |
| `pan-left` | Looking back, memory, reflection |
| `none` | Video clips or static display |

`style` photo filter:

| Value | Use |
| --- | --- |
| `vibrant` | Bright school activities, celebration, outdoor scenes |
| `vintage` | Memories, preparation, nostalgic tone |
| `sepia` | Historical or warm retrospective moments |
| `film` | Dynamic highlights, performance, sports |
| `bw` | Serious reflection, farewell, emotional turn |
| `none` | Natural color or video clips |

Use `style` on photo media items to request a filter. For teaching-record videos, prefer `none` for accurate classroom documentation and `vibrant` for clear activity highlights. Keep `style: "none"` on videos unless the renderer explicitly supports video filters.

`frame`:

| Value | Use |
| --- | --- |
| `polaroid` | Class memories, portraits, group photos |
| `film_strip` | Highlights, performances, action sequences |
| `thin_white` | Clean premium photo border |
| `shadow_card` | Layered scrapbook/card look |
| `none` | Clean documentary or video clips |

`transition`:

| Value | Use |
| --- | --- |
| `dissolve` | Same scene, warm continuity |
| `slide_left` | Moving forward or changing location |
| `slide_right` | Arrival, progression, reveal |
| `zoom_cut` | Peak/highlight impact |
| `whip_pan` | Fast activity transition |
| `flash_white` | Peak beat, applause, stage moment |
| `match_cut` | Similar composition or action |
| `fade` | Opening, closing, emotional pauses |

`titlecard.template`:

| Value | Use |
| --- | --- |
| `cinematic_blur` | Blurred enlarged photo background, premium opening |
| `paper_memory` | Warm photo-paper memory style |
| `ceremony_gold` | Formal school ceremony style |
| `clean_documentary` | Teaching record style |
| `chalkboard` | Classroom/younger grades |

`chapter_marker.style`:

| Value | Use |
| --- | --- |
| `lower_third_line` | Professional small chapter label |
| `date_stamp` | Trip/date memory marker |
| `small_badge` | Cute or class activity |
| `none` | No visible marker |

`sound_cue`:

| Value | Use |
| --- | --- |
| `soft_hit` | Title reveal |
| `soft_whoosh` | Gentle transition |
| `beat_hit` | Highlight cut |
| `camera_click` | Photo stack/scrapbook moment |
| `none` | No sound cue |

## Preset Combinations

| Scene type | rhythm | layout | color_look | transition |
| --- | --- | --- | --- | --- |
| Opening title | warm_slow | full_bleed | warm_cinematic | fade |
| Preparation/instructions | documentary | full_bleed | bright_documentary | dissolve |
| Arrival/group photo | warm_slow | photo_stack | lively_school | slide_right |
| Dynamic activity | lively_fast | full_bleed | lively_school | whip_pan |
| Peak moment | cinematic_peak | film_frame | lively_school | zoom_cut |
| Exploration/detail | documentary | detail_focus | bright_documentary | match_cut |
| Reflection/farewell | emotional_pause | scrapbook | warm_cinematic | fade |
| Formal ceremony | warm_slow | full_bleed | ceremony_gold | dissolve |
| Video clip | documentary | letterbox_video | natural | zoom_cut |

## Duration Heuristics

For a target duration:

- Count title cards first: premium title cards are usually 4-6 seconds each.
- Add chapter markers over existing media, not as separate long scenes.
- In `subtitle-only`, estimate photos at 4-6 seconds each.
- In `voice`, keep narration concise: about 12-18 Chinese characters per 3 seconds.
- Use faster 2.5-4 second cuts in peak scenes.
- Use slower 5-7 second cuts in reflection scenes.
- Prefer fewer strong images over using every image.
- Keep the final result within about 15% of the requested duration.
