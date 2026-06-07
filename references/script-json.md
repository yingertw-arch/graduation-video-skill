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
  "font": null,
  "font_size": 42,
  "duration_per_image": 5,
  "visual_profile": "warm_cinematic",
  "safe_area": {"subtitle_bottom": 120, "title_margin": 160},
  "audio": {"bgm_volume": 0.25, "tts_volume": 1.0, "bgm_fadeout": 3, "sound_cues": false},
  "render": {"preset": "veryfast", "crf": 23, "threads": 0, "transition_duration": 0.35},
  "scenes": []
}
```

`mode`: `voice` or `subtitle-only`.

`audio.bgm_fadeout`: seconds of ending BGM fade-out (0–30, default `3`). Set `0` to let the
track finish without a fade — useful in song-first MV mode where the song should end cleanly.

In `subtitle-only` mode, `narration` is rendered as a burned-in subtitle, so it doubles as the
on-screen lyric line for song-first MVs (see [`mv-mode.md`](mv-mode.md)).

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

`background_file` must be an image file (`.jpg`, `.jpeg`, `.png`, `.heic`). Do not use video files as title-card backgrounds in the baseline renderer.

## Photo or video item

```json
{
  "file": "IMG_001.jpg",
  "narration": "今天，我們帶著笑容和勇氣，走向下一段旅程。",
  "duration": 5,
  "layout": "photo_stack",
  "motion": "auto",
  "effect": "auto",
  "style": "vibrant",
  "frame": "thin_white",
  "transition": "auto",
  "transition_duration": 0.6,
  "pause_after": 0,
  "sound_cue": "none"
}
```

Set `allow_repeat: true` only when a repeated photo is intentional. The validator warns when the same media file appears more than once.

For videos, use `layout: "letterbox_video"` for vertical or non-16:9 clips and `style: "none"` unless the renderer supports video filters.

Each media item is also the photo-to-script mapping unit. When showing the script preview, list each `file` or `files` group beside its narration/subtitle, duration, layout, motion, and transition so the user can approve which photo matches which sentence.

Video clips are supported as single media items with `file`, for example `{"file": "clip.mp4", "layout": "letterbox_video", "duration": 8}`. The baseline renderer trims the clip to `min(script duration, real clip duration)`.

## Multi-photo layouts

Use `files` instead of `file` when one beat should show several photos together. `files` is image-only; do not put `.mp4`, `.mov`, or `.m4v` inside `files`.

```json
{
  "files": ["IMG_001.jpg", "IMG_002.jpg", "IMG_003.jpg", "IMG_004.jpg"],
  "narration": "每一張笑臉，都成為今天最亮的風景。",
  "duration": 5,
  "layout": "video_wall",
  "motion": "auto",
  "transition": "slide_left"
}
```

Recommended layouts:

- `video_wall` / `grid_2x2`: 4 photos, energetic activities, performances, field trips.
- `mosaic`: 3 photos, one main image plus two detail moments.
- `split_two`: 2 photos, before/after or process/result.
- `photo_stack`: 2-3 photos, warm memory or class-life sequence.

## Automatic effect selection

Use `motion: "auto"` and `transition: "auto"` when the renderer should infer effects:

- Wide photo: usually pan left/right.
- Portrait photo: usually slow pull back to preserve the subject.
- Square/group photo: usually slow push in.
- `lively_fast` scene: slide/zoom-cut style transitions.
- `emotional_pause` scene: fade transition and slower motion.
- `pause_after`: short beat pause, usually `0.2`-`0.8` seconds.
- Keep default `transition_duration` around `0.25`-`0.45`; longer overlaps can feel muddy and make rendering slower.

## Allowed values

- `visual_profile` / `color_look`: `warm_cinematic`, `bright_documentary`, `lively_school`, `ceremony_gold`, `soft_pastel`, `natural`
- `story_role`: `hook`, `setup`, `peak`, `turn`, `echo`
- `rhythm`: `warm_slow`, `lively_fast`, `cinematic_peak`, `emotional_pause`, `documentary`
- `layout`: `full_bleed`, `photo_stack`, `split_two`, `scrapbook`, `film_frame`, `detail_focus`, `letterbox_video`, `video_wall`, `grid_2x2`, `mosaic`
- `motion`: `auto`, `slow_push_in`, `slow_pull_back`, `pan_right`, `pan_left`, `parallax_soft`, `handheld_soft`, `none`
- `effect`: `auto`, `zoom-in`, `pan-right`, `pan-left`, `fade-in`, `blur-in`, `pop-in`, `none`
- `style`: `vibrant`, `vintage`, `sepia`, `film`, `bw`, `none`
- `frame`: `polaroid`, `film_strip`, `thin_white`, `shadow_card`, `none`
- `transition`: `auto`, `dissolve`, `slide_left`, `slide_right`, `zoom_cut`, `whip_pan`, `flash_white`, `match_cut`, `fade`, `hold`
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
- For video clips, validator can use `--probe-video-durations` to estimate actual rendered duration as `min(script duration, real clip duration)` when `ffprobe` is available.
