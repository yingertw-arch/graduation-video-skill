---
name: graduation-video
description: Create polished school montage videos from photo and video folders for graduation ceremonies, teaching records, achievement showcases, school anniversaries, field trips, class events, and ceremony playback. Use when the user asks to make a graduation video, teaching-record video, school activity video, class event montage, 學校活動影片, 畢業影片, 教學紀錄影片, 成果發表影片, 校慶影片, 校外教學影片, 班級回憶影片, or a narrated/subtitled MP4 from school photos and clips. Includes media inventory, script planning, privacy checks, narration/subtitles, BGM guidance, validation, rendering, and QA. Do not trigger for unrelated generic video editing unless it is clearly a school or class activity montage.
---

# Graduation Video

Create a school-event MP4 from a folder of photos/videos. First inventory the material, then draft a `script.json`, get approval, validate, render, and QA the output.

## First response

If any required input is missing, ask for all missing items at once before inventorying or rendering:

1. Material folder path.
2. Video type: graduation, teaching record, achievement showcase, school anniversary, field trip, class event, or other school activity.
3. Video title, school/class name, and date/semester if available.
4. Target duration.
5. Output mode: `voice` for TTS + subtitles, or `subtitle-only`.
6. Background music: MP3 path, Suno prompt, no music, or decide later.
7. Tone: warm, lively, documentary, grand, cute, cinematic, or teacher-written.
8. Visual ambition: simple, polished, or cinematic. Default: polished.

If enough information is already present, restate the chosen folder, title, duration, output mode, music, tone, and ambition before proceeding. Never assume the current workspace is the material folder.

## Required approval gate

Before final rendering, always show a concise script preview and wait for explicit confirmation. This is mandatory for teaching-record videos because the narration and privacy choices must be teacher-approved.

Preview should include:

- Scene table: scene name, story role, media count, rhythm, estimated duration, sample narration.
- Actual title-card and narration/subtitle text.
- Skipped/problem files and privacy warnings.

Save `script.json` before approval only if the user asks for a draft file.

## Workflow

1. **Inventory material**
   - Run `scripts/inventory_media.py <folder> --output media_inventory.json` when practical.
   - Supported media: `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.m4v`.
   - Sort by EXIF/date taken when available, then modified time, then filename.
   - Flag tiny, empty, unsupported, duplicate-looking, and privacy-risk filenames.

2. **Plan story**
   - Use a 5-part arc: hook, setup, peak, turn, echo.
   - Prefer fewer strong images over using everything.
   - Avoid naming students unless names are provided and safe.
   - Do not include private details from screenshots, IDs, grades, medical records, forms, addresses, or phone numbers.

3. **Design visual language**
   - Pick one global `visual_profile`.
   - Use motion title cards, not plain black screens, unless the user asks for a simple slideshow.
   - Vary layouts: `full_bleed`, `split_two`, `photo_stack`, `scrapbook`, `film_frame`, `detail_focus`, `letterbox_video`.
   - Use transitions and sound cues as story punctuation, not on every clip.
   - Read `references/pro-design.md` only when detailed presets are needed.

4. **Create `script.json`**
   - Follow `references/script-json.md`.
   - Use relative filenames in `media.file` and title-card `background_file`.
   - Match total duration within 15% of the requested target unless the user approves otherwise.
   - In `subtitle-only`, set durations explicitly.

5. **Validate**
   - Run: `python scripts/validate_script.py <script.json> --media-root <folder> --target-duration <seconds>`.
   - Fix all errors. Warnings may remain only if explained.

6. **Render**
   - Use bundled `scripts/generate_video.py` for a deterministic baseline renderer.
   - If the user has a more advanced renderer, use it instead after confirming its path.
   - Do not install missing packages globally without approval; prefer a local virtual environment.

7. **Music and rights**
   - If using an existing music file, confirm it exists.
   - For public playback or upload, remind the user to use music they are allowed to publish.
   - If the user wants generated music, adapt a prompt from `references/video-generation.md`.

8. **QA the MP4**
   - Confirm file exists and size is plausible.
   - Use `ffprobe` if available to check duration, resolution, FPS, and audio streams.
   - Extract a few frames if possible and inspect title cards, cropping, subtitles, and chapter markers.
   - Report output path, duration, warnings, and suggested polish.

## Defaults

- Output: 1920x1080 MP4, 24 fps.
- Font on Windows: `C:/Windows/Fonts/msjh.ttc`.
- TTS voice: `zh-TW-HsiaoChenNeural`; offer `zh-TW-YunJheNeural` for male voice.
- Visual profiles: graduation `warm_cinematic`, teaching record `bright_documentary`, activities `lively_school`, ceremonies `ceremony_gold`.
- Photo duration: 4-6 seconds; peak scenes 2.5-4 seconds; reflection 5-7 seconds.
- BGM volume under narration: 20-30%, fade out last 3 seconds.

## Guardrails

- Never write API keys, service credentials, passwords, or private configs into generated files.
- Do not overwrite original media.
- Keep generated files in the material folder or a clearly named output folder.
- Preserve student privacy: avoid face labels, IDs, grades, phone numbers, addresses, and medical details unless explicitly required and safe.
