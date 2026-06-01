---
name: graduation-video
description: Create professional school activity montage videos from photo/video folders for graduation ceremonies, teaching records, achievement showcases, school anniversaries, field trips, class events, and ceremony playback. Use when the user asks to make a graduation video, teaching-record video, achievement showcase video, school anniversary video, school activity photo video, class event montage, or uses Chinese phrases such as "?Ｘ平?貊旨敶梁?", "?飛蝝?蔣??, "???潸”敶梁?", "?⊥敶梁?", "瘣餃??抒?敶梁?", "?飛?⊥暑????蔣??. Include narration, subtitles, BGM, motion title cards, chapter markers, visual layouts, color looks, transitions, sound cues, script validation, rendering, and MP4 QA. Do not trigger for unrelated generic video editing unless it is clearly a school/class activity montage.
---

# Graduation Video

Build a polished school-event montage from a folder of photos/videos. Produce a confirmed `script.json`, validate it, then render or guide rendering to MP4.

## First Response

For short requests such as "make a teaching record video" or "???????", always ask for the required inputs before inventorying or rendering. Ask for all required inputs at once if missing:

1. Material folder path.
2. Video type: graduation, teaching record, achievement showcase, school anniversary, field trip, class event, or other school activity.
3. Video title, school/class name, and date or semester if available.
4. Target duration.
5. Output mode: `voice` for TTS plus subtitles, or `subtitle-only`.
6. Background music choice: existing MP3, Suno prompt, no music, or decide later.
7. Preferred tone: warm, lively, documentary, grand, cute, cinematic, or teacher-written.
8. Visual ambition: simple, polished, or cinematic. Default to polished.

If the user already gave enough information, restate the selected material folder, video title, duration, output mode, music, tone, and visual ambition before proceeding. Do not assume a folder from the current workspace when the user only gives a generic request.

Before any rendering, always show the script for approval. For teaching-record videos, this approval gate is mandatory even if the user provided a folder and music. Do not create the final MP4 until the user explicitly confirms the script.

## Professional Design Rules

Do not make a plain slideshow unless the user asks for one. Build a visual system:

- Use motion title cards, not plain black screens with text.
- Vary layouts across the film: full bleed, split screen, photo stack, scrapbook, film frame, detail focus.
- Assign scene-level rhythm: warm slow, lively fast, cinematic peak, emotional pause, documentary.
- Use a consistent color look for the whole video, with minor scene variation only when useful.
- Add photo filters deliberately (`style`) so still images feel polished: use natural, vibrant, vintage, sepia, film, or bw according to the scene purpose.
- Add chapter markers every 20-40 seconds for longer videos.
- Place transitions by story function, not randomly.
- Add optional sound cues for title reveals, peak cuts, and gentle transitions when the renderer supports them.

## Workflow

1. Inventory the folder.
   - Read supported media: `.jpg`, `.jpeg`, `.png`, `.heic`, `.mp4`, `.mov`, `.m4v`.
   - Sort by EXIF/date taken when available, otherwise modified time, then filename.
   - Flag tiny, corrupted, duplicate-looking, or unsupported files.
   - For very large folders, create a shortlist that fits the target duration.

2. Analyze visuals.
   - Review images/videos in small batches.
   - For each usable item, infer content, action, emotion, quality, likely scene, layout, and narration.
   - Avoid naming students unless the user provides names.
   - Do not include private/sensitive details visible in screenshots, documents, IDs, or student records.

3. Draft a 5-part story arc.
   - Hook: premium opening motion title, 10-15%.
   - Setup: preparation, arrival, context, 20-25%.
   - Peak: strongest activity moments, 30-35%.
   - Turn: reflection, growth, gratitude, or emotional shift, 15-20%.
   - Echo: closing motion title, 5-10%.
   - Keep main title-card text short; use subtitle/date fields for details.

4. Design the video language.
   - Pick one global `visual_profile`.
   - Assign each scene a `rhythm`, `color_look`, optional `chapter_marker`, and transition strategy.
   - Assign each photo media item a `layout`, `motion`, photo filter `style`, `transition`, and optional `sound_cue`.
   - Use restrained filter changes: keep teaching-record videos clean and readable, but apply subtle `vibrant` for activity peaks, `film` for highlights, `vintage`/`sepia` for memory sections, and `bw` only for intentional reflection.
   - Use transitions as story punctuation: gentle transitions within a scene, stronger transitions only for chapter changes, peak beats, or matched compositions.
   - Use `references/pro-design.md` for presets and examples.

5. Draft the script and ask for approval before rendering.
   - Show a concise scene table: scene name, media count, rhythm, visual profile, sample narration, estimated duration.
   - Also show the actual narration/title-card text that will be used, or a readable `script.json` preview when practical.
   - Mention skipped/problem files.
   - Wait for explicit user confirmation before creating the final MP4. For teaching-record videos, do not bypass this approval gate.

6. Create or update `script.json` only after approval, unless the user specifically asks to save a draft script first.
   - Follow `references/script-json.md`.
   - Use relative filenames in `media.file`, not absolute paths.
   - Match total duration to the target within about 15% unless the user approves otherwise.
   - In `subtitle-only`, set image durations explicitly and keep narration as subtitle text.

7. Validate before rendering.
   - Run `scripts/validate_script.py <script.json> --media-root <folder>`.
   - Fix every error. Warnings may remain only if explained to the user.

8. Prepare music.
   - If the user wants Suno, provide one prompt from `references/video-generation.md`.
   - If using existing music, confirm the file exists.
   - For school public playback or upload, remind the user to use music they are allowed to publish.

9. Render or hand off rendering.
   - Prefer an existing local generator if the user has one.
   - If a generator path is not known, locate it from user context or ask for it.
   - Use PowerShell-friendly commands on Windows.
   - Do not install dependencies globally without user approval; check first.

10. Quality check the MP4.
   - Confirm file exists and size is plausible.
   - Use `ffprobe` when available to check duration, resolution, fps, and audio streams.
   - Capture a few still frames if possible and inspect title cards, layouts, cropping, subtitle placement, and chapter markers.
   - Report output path, duration, warnings, and next suggested polish.

## Key References

- `references/script-json.md`: schema, allowed values, scene/media examples.
- `references/pro-design.md`: motion title, layout, rhythm, transition, color, and sound-cue presets.
- `references/video-generation.md`: dependency checks, PowerShell commands, Suno prompts, QA checklist.
- `scripts/validate_script.py`: deterministic validator for `script.json` and media references.

## Defaults

- Output: 1920x1080 MP4, 24 fps.
- Font on Windows: `C:/Windows/Fonts/msjh.ttc`.
- TTS voice: `zh-TW-HsiaoChenNeural`; offer `zh-TW-YunJheNeural` for male voice.
- Global visual profile: `warm_cinematic` for graduation, `bright_documentary` for teaching record, `lively_school` for activities, `ceremony_gold` for formal ceremonies.
- Image duration: 4-6 seconds in `subtitle-only`; in `voice`, duration follows narration/TTS timing when the renderer supports it.
- Music mix: keep BGM around 20-30% under narration, fade out in the last 3 seconds.

## Guardrails

- Never write API keys, service credentials, or private configs into generated files.
- Do not overwrite original media.
- Keep generated working files in the material folder or a clearly named output folder.
- Preserve student privacy: avoid face labeling, ID numbers, grades, phone numbers, addresses, or medical details unless explicitly required and safe.
- For unclear requests like "make a video", only use this skill when the surrounding context is a school/class activity montage.
