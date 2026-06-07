---
name: graduation-video
description: Create polished school montage videos from photo and video folders for graduation ceremonies, teaching records, achievement showcases, school anniversaries, field trips, class events, and ceremony playback. Use when the user asks to make a graduation video, teaching-record video, school activity video, class event montage, school photo/video montage, 學校活動影片, 畢業影片, 教學紀錄影片, 成果發表影片, 校慶影片, 校外教學影片, 班級回憶影片, or a narrated/subtitled MP4 from school photos and clips. Also supports a song-first MV mode that turns a song plus timed lyrics (LRC or section times) into a lyrics-to-picture music video where each lyric line/section is matched to a photo or clip and the song is the main audio (畢業歌 MV, 用歌詞配照片, 歌曲 MV). Includes media inventory, photo-to-script mapping, Suno prompt generation from the approved script, privacy checks, narration/subtitles, BGM/MP3 review, automated validation, automated rendering, and QA. Do not trigger for unrelated generic video editing unless it is clearly a school or class activity montage.
---

# Graduation Video

Create a school-event MP4 from a folder of photos/videos. First inventory the material, map photos to script lines, draft a `script.json`, get approvals, generate/adapt a Suno prompt when needed, then automatically validate, render, and QA the output after the user says to start final generation.

## First response

First pick the mode, because it changes where the timeline comes from:

- **Mode A — material-first (default):** photos/clips drive the story; you write narration/subtitles and add BGM afterward. Use this when the user has a folder and wants a montage. Follow the phased questions and workflow below.
- **Mode B — song-first MV:** the user provides a song (+ lyrics or section times) and the lyric timeline is the skeleton; you fill each lyric line/section with a matching photo or clip, and the song itself is the main audio. Use this when the user says things like "用這首歌做 MV", "跟著歌詞配照片", or gives a Suno graduation song. See "Mode B — song-first MV" below.

If the request is ambiguous, ask which mode. Then continue with the phased questions (Mode A) or the three MV questions (Mode B).

Avoid overwhelming the user with a long questionnaire. Ask in phases:

**Phase 1 — required to begin inventory and planning**

1. Material folder path.
2. Video type: graduation, teaching record, achievement showcase, school anniversary, field trip, class event, or other school activity.
3. Video title, school/class name, and date/semester if available.
4. Target duration.

**Phase 2 — ask after inventory or before script approval**

5. Output mode: `voice` for TTS + subtitles, or `subtitle-only`.
6. Background music: MP3 path, Suno prompt, no music, or decide later.
7. Tone: warm, lively, documentary, grand, cute, cinematic, or teacher-written.
8. Visual ambition: simple, polished, or cinematic. Default: polished.

If the user gives only a short request, ask only Phase 1 first unless Phase 2 answers are necessary for the immediate next step.

If enough information is already present, restate the chosen folder, title, duration, output mode, music, tone, and ambition before proceeding. Never assume the current workspace is the material folder.

## Required approval gates

Before final rendering, always show a concise preview and wait for explicit confirmation. This is mandatory for teaching-record videos because the narration and privacy choices must be teacher-approved.

Preview should include:

- A teacher-proofing media review list from `media_inventory.json` and `media_review.csv`, grouped into keep / duplicate / quality concern / privacy concern / unsuitable.
- A clear duplicate-photo decision: repeated files or visually similar photos are removed unless the user explicitly marks them `allow_repeat`.
- Scene table: scene name, story role, media count, rhythm, estimated duration, sample narration.
- Actual title-card and narration/subtitle text.
- A photo-to-script mapping table: media filename(s), scene, narration/subtitle sentence, duration, layout, motion, transition.
- Skipped/problem files and privacy warnings.
- Music plan: Suno prompt or selected MP3/BGM path, tone, tempo, and rights reminder.

Do not render until all required approvals are complete:

1. **Photo/material approval**: usable media list, duplicate removals, skipped/problem files, unsuitable-photo decisions, and privacy warnings are accepted.
2. **Script approval**: title cards, narration/subtitles, scene order, photo-to-script mapping, transition style, and filter plan are accepted.
3. **Draft video approval**: render a low-resolution `--draft` MP4 when practical, then correct repeated photos, unsuitable photos, awkward transitions, subtitle placement, or pacing before full output.
4. **Music approval**: Suno prompt is accepted before generating music, and the final MP3/BGM file is provided and accepted before final rendering.

Save `script.json` before approval only if the user asks for a draft file.

## Fully automated final generation

After the approvals above are complete, when the user says "start generating", "開始生成影片", "產出影片", or similar, do not ask the user to run commands manually. Codex must automatically:

1. Locate the approved `script.json`, material folder, and approved MP3/BGM file when one is required.
2. Confirm files exist without asking for manual checks.
3. Run `scripts/validate_script.py` with `--media-root`, target duration, and `--probe-video-durations` when `ffprobe` is available.
4. If validation has errors, fix the script or report the specific blocker. Do not render with errors.
5. Run `scripts/generate_video.py` with `--script`, `--media-root`, and `--bgm` when music is approved.
6. Run QA checks automatically when tools are available: file existence/size, `ffprobe`, and optional frame extraction with `ffmpeg`.
7. Report only the final MP4 path, duration/resolution/audio findings, warnings, and next polish suggestions.

## Workflow

1. **Inventory material**
   - Run `scripts/inventory_media.py <folder> --output media_inventory.json --review-csv media_review.csv` when practical.
   - Supported media: `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.m4v`.
   - Sort by EXIF/date taken when available, then modified time, then filename.
   - Flag tiny, empty, unsupported, exact duplicates, visually similar duplicates, low-resolution images, awkward aspect ratios, unreadable files, and privacy-risk filenames.
   - Treat duplicate and unsuitable-photo warnings as teacher-proofing blockers: remove or replace them before final render unless explicitly approved.

2. **Plan story**
   - Use a 5-part arc: hook, setup, peak, turn, echo.
   - Prefer fewer strong images over using everything.
   - Build a photo-to-script mapping: each media item or `files` group must map to a specific narration/subtitle sentence or intentional silent beat.
   - Avoid naming students unless names are provided and safe.
   - Do not include private details from screenshots, IDs, grades, medical records, forms, addresses, or phone numbers.

3. **Design visual language**
   - Pick one global `visual_profile`.
   - Use motion title cards, not plain black screens, unless the user asks for a simple slideshow.
   - Every photo should have an explicit or automatic entrance/motion choice: `motion: "auto"` is acceptable and lets the renderer infer pan/zoom from the image.
   - Vary layouts: `full_bleed`, `split_two`, `photo_stack`, `scrapbook`, `film_frame`, `detail_focus`, `letterbox_video`, `video_wall`, `grid_2x2`, `mosaic`.
   - Use `files: [...]` only for multi-photo layouts such as TV-wall/video wall, grid, mosaic, or split-screen sequences; `files` must contain images only.
   - Use video clips as single `file` media items with `layout: "letterbox_video"` when needed.
   - Give every media item a story-appropriate `transition`; use `transition: "auto"` when the renderer should choose by rhythm. Prefer `dissolve`/`fade` for teaching records and avoid repeated strong transitions.
   - Give photo media a restrained `style` filter only when it improves clarity or mood; keep classroom proof/documentation photos `none` or subtle `vibrant`.
   - Use `pause_after` for intentional beat pauses, emotional stops, or comma-like visual punctuation.
   - Use sound cues as story punctuation, not on every clip.
   - Read `references/pro-design.md` only when detailed presets are needed.

4. **Create `script.json`**
   - Follow `references/script-json.md`.
   - Use relative filenames in `media.file`, `media.files`, and title-card `background_file`.
   - Keep `media.file`/`media.files` aligned with the approved photo-to-script mapping.
   - Match total duration within 15% of the requested target unless the user approves otherwise.
   - In `subtitle-only`, set durations explicitly.

5. **Generate Suno prompt when requested**
   - Generate the Suno prompt from the approved script's story arc, emotional curve, target duration, tone, and public-playback context.
   - Include whether the music should be instrumental or vocal, language if vocal, mood, instrumentation, BPM range, and "no copyrighted melody".
   - Wait for prompt approval before the user creates/provides the Suno MP3.

6. **Validate**
   - Run: `python scripts/validate_script.py <script.json> --media-root <folder> --target-duration <seconds> --probe-video-durations` when `ffprobe` is available.
   - Fix all errors. Warnings may remain only if explained.

7. **Draft and render**
   - Before a full render, produce a fast draft preview when practical: `scripts/generate_video.py --draft ...`. Use it for proofreading repeated photos, unsuitable photos, subtitle placement, transition smoothness, and pacing.
   - Use bundled `scripts/generate_video.py` for a deterministic baseline renderer.
   - The baseline renderer supports automatic image-based motion selection, slow zoom/pan, video-wall/grid/mosaic still layouts, fade/dissolve/slide-like transitions, and short pauses.
   - Once draft approval and final approvals are complete, execute full rendering automatically; do not hand the command to the user unless blocked by permissions or missing dependencies.
   - For long videos, optimize by rendering a draft first, keeping resolution/FPS modest until approval, using fewer repeated stills, grouping related photos into multi-photo layouts, and using renderer `render.preset`/`threads` settings for final output.
   - If the user has a more advanced renderer, use it instead after confirming its path.
   - Do not install missing packages globally without approval; prefer a local virtual environment.

8. **Music and rights**
   - If using an existing music file, confirm it exists.
   - For public playback or upload, remind the user to use music they are allowed to publish.
   - If the user wants generated music, adapt a prompt from `references/video-generation.md` based on the approved script, then wait for the final MP3 before rendering.

9. **QA the MP4**
   - Confirm file exists and size is plausible.
   - Use `ffprobe` when available to check duration, resolution, FPS, and audio streams.
   - Extract a few frames when possible and inspect title cards, cropping, subtitles, transitions, and chapter markers.
   - Report output path, duration, warnings, and next suggested polish.

## Mode B — song-first MV

The song's lyric timeline is the skeleton. The renderer does not change; the timeline comes from `scripts/lyrics_to_script.py` and the song is the main audio. Read `references/mv-mode.md` for input formats, chorus detection, and how durations are derived.

**Three MV questions (ask before building the skeleton):**

1. Show lyric subtitles on screen, or no on-screen lyrics? (controls `--no-lyrics`)
2. Line-by-line correspondence (one photo per lyric line) or section correspondence (one photo held per verse/chorus block)? (controls `--granularity line|section`)
3. For the chorus, prioritize the most moving graduation photos / whole-class photos / activity highlights? (the skeleton marks chorus items so you can place hero media there)

**Mode B workflow:**

1. **Get the song + lyric timing.** Either an LRC file (`[mm:ss.xx]lyric`) or, for Suno songs without an LRC, a sections JSON (`[{"time": "0:15", "text": "..."}, ...]`) where the teacher marks a few section start times. Get the song file too (or its duration in seconds).
2. **Inventory the material folder** as in Mode A so you know which photos/clips are available and which are privacy risks.
3. **Build the skeleton:** run `scripts/lyrics_to_script.py` with `--lrc` or `--sections`, `--song` (or `--song-duration`), the chosen `--granularity`, and `--no-lyrics` if subtitles are off. This produces a `subtitle-only` `script.json` whose total length matches the song, with `audio.bgm_volume: 1.0` (the song is the main audio) and each item's `duration` derived from the lyric timestamps. Chorus items carry `_section: "chorus"` and a punchier `zoom_cut` transition.
4. **Fill the media.** Each item's `file` is a blank placeholder (with `_lyric`/`_lyrics`/`_start` annotations). Map a photo or clip to each lyric line/section based on its content; put the strongest hero/class/highlight media on the chorus items. You can also pre-fill sequentially with `--media-list`/`--media-dir` and then adjust.
5. **Get approvals** using the same gates below — for Mode B, music approval means confirming the song + lyric timing, since the song is the audio.
6. **Validate** the filled `script.json` (`scripts/validate_script.py`). Total duration should already be within range because it equals the song length.
7. **Render** with `scripts/generate_video.py`, passing the song as `--bgm`. Set `audio.bgm_fadeout` to 0 to let the song finish cleanly, or a few seconds to fade out.
8. **QA** the MP4 as in Mode A: confirm total length ≈ song length, the audio track is the song, and subtitles match the lyrics when shown.

## Defaults

- Output: 1920x1080 MP4, 24 fps.
- Font: leave `font` unset by default and let the renderer choose the first available CJK-capable font. On Windows it may use `C:/Windows/Fonts/msjh.ttc`; on macOS/Linux it should use installed CJK/Noto fonts when available.
- TTS voice: `zh-TW-HsiaoChenNeural`; offer `zh-TW-YunJheNeural` for male voice. Voice mode uses `edge-tts`, which requires the `edge-tts` Python package and internet access to Microsoft's online TTS service; it does not require the Edge browser itself. If unavailable, use `subtitle-only`.
- Visual profiles: graduation `warm_cinematic`, teaching record `bright_documentary`, activities `lively_school`, ceremonies `ceremony_gold`.
- Photo duration: 4-6 seconds; peak scenes 2.5-4 seconds; reflection 5-7 seconds.
- BGM volume under narration: 20-30%, fade out last 3 seconds.

## Guardrails

- Never write API keys, service credentials, passwords, or private configs into generated files.
- Do not overwrite original media.
- Keep generated files in the material folder or a clearly named output folder.
- Preserve student privacy: avoid face labels, IDs, grades, phone numbers, addresses, and medical details unless explicitly required and safe.
